"""RabbitMQ worker for background tasks."""

import json
import os
import re

import pika
import psycopg
from psycopg.types.json import Jsonb
from queries_2 import QUERIES


EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"
SOURCE = "llm_extend_applicant_data_run.jsonl"
DATA_FILE = "/data/llm_extend_applicant_data_run.jsonl"


def open_rabbit_channel():
    params = pika.URLParameters(os.environ["RABBITMQ_URL"])
    rabbit_conn = pika.BlockingConnection(params)
    channel = rabbit_conn.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    # Backpressure with one message at a time
    channel.basic_qos(prefetch_count=1)

    return rabbit_conn, channel


def get_last_seen(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT last_seen FROM ingestion_watermarks WHERE source = %s",
            (SOURCE,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def update_last_seen(conn, last_seen):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion_watermarks (source, last_seen, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (source)
            DO UPDATE SET
                last_seen = EXCLUDED.last_seen,
                updated_at = now();
            """,
            (SOURCE, last_seen),
        )


def result_id(url):
    if not url:
        return None
    match = re.search(r"/result/(\d+)", url)
    return int(match.group(1)) if match else None


def load_new_records(since):
    since_id = int(since) if since else 0
    records = []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)
            current_id = result_id(record.get("url"))

            if current_id and current_id > since_id:
                records.append(record)

    return records


def insert_applicants(conn, records):
    insert_sql = """
        INSERT INTO applicants (
            program, comments, date_added, url, status, term,
            us_or_international, gpa, gre, gre_v, gre_aw, degree,
            llm_generated_program, llm_generated_university
        )
        VALUES (
            %(program)s, %(comments)s, %(date_added)s, %(url)s, %(status)s, %(term)s,
            %(us_or_international)s, %(gpa)s, %(gre)s, %(gre_v)s, %(gre_aw)s,
            %(degree)s, %(llm_generated_program)s, %(llm_generated_university)s
        )
        ON CONFLICT (url) DO NOTHING;
    """

    with conn.cursor() as cur:
        for record in records:
            cur.execute(
                insert_sql,
                {
                    "program": record.get("program"),
                    "comments": record.get("comments"),
                    "date_added": record.get("date_added"),
                    "url": record.get("url"),
                    "status": record.get("status"),
                    "term": record.get("term"),
                    "us_or_international": record.get("US/International"),
                    "gpa": record.get("GPA") or None,
                    "gre": record.get("GRE") or None,
                    "gre_v": record.get("GRE V") or None,
                    "gre_aw": record.get("GRE AW") or None,
                    "degree": record.get("Degree"),
                    "llm_generated_program": record.get("llm-generated-program"),
                    "llm_generated_university": record.get("llm-generated-university"),
                },
            )


def handle_scrape_new_data(conn, payload):
    since = payload.get("since") or get_last_seen(conn)
    records = load_new_records(since)

    if not records:
        return

    insert_applicants(conn, records)

    max_seen = max(result_id(record.get("url")) for record in records)
    update_last_seen(conn, str(max_seen))


# def handle_recompute_analytics(conn, payload):
#     with conn.cursor() as cur:
#         cur.execute("SELECT COUNT(*) FROM applicants;")
# def handle_recompute_analytics(conn, payload):
#     with conn.cursor() as cur:
#         for query in QUERIES:
#             params = query.get("params")

#             if params is None:
#                 cur.execute(query["sql"])
#             else:
#                 cur.execute(query["sql"], params)

#             rows = cur.fetchall()
#             columns = [desc.name for desc in cur.description]

#             print(query["number"], columns, rows)
def handle_recompute_analytics(conn, payload):
    with conn.cursor() as cur:
        for query in QUERIES:
            params = query.get("params")

            if params is None:
                cur.execute(query["sql"])
            else:
                cur.execute(query["sql"], params)

            columns = [desc.name for desc in cur.description]
            rows = [[str(value) if value is not None else None for value in row] for row in cur.fetchall()]

            cur.execute(
                """
                INSERT INTO analytics_results (
                    query_number,
                    question,
                    columns,
                    rows,
                    error,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (query_number)
                DO UPDATE SET
                    question = EXCLUDED.question,
                    columns = EXCLUDED.columns,
                    rows = EXCLUDED.rows,
                    error = EXCLUDED.error,
                    updated_at = now();
                """,
                (
                    query["number"],
                    query["question"],
                    Jsonb(columns),
                    Jsonb(rows),
                    None,
                ),
            )

# Consumes and routes by task kind
TASKS = {
    "scrape_new_data": handle_scrape_new_data,
    "recompute_analytics": handle_recompute_analytics,
}


def process_message(channel, method, properties, body):
    db_conn = psycopg.connect(os.environ["DATABASE_URL"])

    try:
        message = json.loads(body.decode("utf-8"))
        kind = message["kind"]
        payload = message.get("payload", {})

        handler = TASKS[kind]
        handler(db_conn, payload)
        # Commit only on success
        # ack means acknowledge.
        db_conn.commit()
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except Exception:
        # rollback on error
        # nack means negative acknowledge
        db_conn.rollback()
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        raise

    finally:
        db_conn.close()


def main():
    rabbit_conn, channel = open_rabbit_channel()

    channel.basic_consume(
        queue=QUEUE,
        on_message_callback=process_message,
    )

    print("Worker waiting for tasks...")
    channel.start_consuming()


if __name__ == "__main__":
    main()