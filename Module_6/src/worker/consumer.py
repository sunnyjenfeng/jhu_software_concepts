"""RabbitMQ worker for background tasks."""

import json
import os
import re

import pika
import psycopg
from psycopg.types.json import Jsonb
from worker.queries_2 import QUERIES
from worker.scrape import scrape_data
from worker.clean import clean_data

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"
SOURCE = "llm_extend_applicant_data_run.jsonl"
DATA_FILE = "/data/llm_extend_applicant_data_run.jsonl"

def open_rabbit_channel():
    """This opens channel"""
    params = pika.URLParameters(os.environ["RABBITMQ_URL"])
    rabbit_conn = pika.BlockingConnection(params)
    channel = rabbit_conn.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    # Backpressure with one message at a time (prefetch_count=1)
    channel.basic_qos(prefetch_count=1)
    return rabbit_conn, channel

def get_last_seen(conn):
    """This function gets the last seen ID"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT last_seen FROM ingestion_watermarks WHERE source = %s",
            (SOURCE,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def update_last_seen(conn, last_seen):
    """This function updates the last seen ID"""
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
    """This function gets the result id"""
    if not url:
        return None
    match = re.search(r"/result/(\d+)", url)
    return int(match.group(1)) if match else None

def watermark_id(value):
    """This function gets the watermark id"""
    if not value:
        return 0

    extracted_id = result_id(value)
    if extracted_id is not None:
        return extracted_id

    return int(value)


def load_new_records(since):
    """This function loads new records"""
    since_id = watermark_id(since)
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
    """
    This function inserts new applicants data into applicants table
    """
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

def insert_scraped_applicants(conn, records):
    """this function inserts scraped applicants data"""
    insert_sql = """
        INSERT INTO applicants (
            program,
            comments,
            date_added,
            url,
            status,
            term,
            us_or_international,
            gpa,
            gre,
            gre_v,
            gre_aw,
            degree,
            llm_generated_program,
            llm_generated_university
        )
        VALUES (
            %(program)s,
            %(comments)s,
            %(date_added)s,
            %(url)s,
            %(status)s,
            %(term)s,
            %(us_or_international)s,
            %(gpa)s,
            %(gre)s,
            %(gre_v)s,
            %(gre_aw)s,
            %(degree)s,
            %(llm_generated_program)s,
            %(llm_generated_university)s
        )
        ON CONFLICT (url) DO NOTHING;
    """

    inserted_count = 0

    with conn.cursor() as cur:
        for record in records:
            program_name = record.get("Program Name")
            university = record.get("University")

            if program_name and university:
                program = f"{program_name}, {university}"
            else:
                program = program_name or university

            cur.execute(
                insert_sql,
                {
                    "program": program,
                    "comments": record.get("Comments"),
                    "date_added": record.get("Date of Information Added to Grad Cafe"),
                    "url": record.get("URL link to applicant entry"),
                    "status": record.get("Applicant Status"),
                    "term": record.get("Semester and Year of Program Start"),
                    "us_or_international": record.get("International / American Student"),
                    "gpa": record.get("GPA") or None,
                    "gre": record.get("GRE Score") or None,
                    "gre_v": record.get("GRE V Score") or None,
                    "gre_aw": record.get("GRE AW") or None,
                    "degree": record.get("Masters or PhD"),
                    "llm_generated_program": program_name,
                    "llm_generated_university": university,
                },
            )

            if cur.rowcount == 1:
                inserted_count += 1

    return inserted_count

def handle_scrape_new_data(conn, payload):
    """
    If the RabbitMQ task payload includes a "since" value, it uses that. 
    Otherwise, it checks the database table ingestion_watermarks to find the last 
    GradCafe result ID that was already processed.
    """
    # Default is now 3 pages
    start_page = payload.get("start_page", 1)
    end_page = payload.get("end_page", 3)

    raw_records = scrape_data(start_page=start_page, end_page=end_page)
    cleaned_records = clean_data(raw_records)

    inserted_count = insert_scraped_applicants(conn, cleaned_records)
    print(f"Inserted {inserted_count} newly scraped applicants.")

    urls = [
        record.get("URL link to applicant entry")
        for record in cleaned_records
        if record.get("URL link to applicant entry")
    ]

    ids = [result_id(url) for url in urls]
    ids = [value for value in ids if value is not None]

    if ids:
        update_last_seen(conn, str(max(ids)))

def handle_recompute_analytics(conn, _payload):
    """
    runs all the analytics SQL queries and saves their results into the 
    analytics_results table.
    """
    with conn.cursor() as cur:
        for query in QUERIES:
            params = query.get("params")

            if params is None:
                cur.execute(query["sql"])
            else:
                cur.execute(query["sql"], params)

            columns = [desc.name for desc in cur.description]
            rows = [[str(value) if value is not None else None
                     for value in row] for row in cur.fetchall()]

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

def process_message(channel, method, _properties, body):
    """
    the function that handles one RabbitMQ message.
    The message is expected to look something like:
        {
        "kind": "recompute_analytics",
        "payload": {}
         }
    """
    # First, it opens a PostgreSQL connection using DATABASE_URL from the environment.
    db_conn = psycopg.connect(os.environ["DATABASE_URL"])  # pylint: disable=no-member
    # Then it tries to process the message
    try:
        message = json.loads(body.decode("utf-8"))
        kind = message["kind"]
        payload = message.get("payload", {})

        handler = TASKS[kind]
        handler(db_conn, payload)
        # Commit only on success
        # ack means acknowledge.
        db_conn.commit()  # pylint: disable=no-member
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except Exception:
        # rollback on error
        # nack means negative acknowledge
        db_conn.rollback()  # pylint: disable=no-member
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        raise

    finally:
        db_conn.close()  # pylint: disable=no-member


def main():
    """main function"""
    rabbit_conn, channel = open_rabbit_channel()
    _ = rabbit_conn

    channel.basic_consume(
        queue=QUEUE,
        on_message_callback=process_message,
    )

    print("Worker waiting for tasks...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
