
"""This notebook use the jsonl data shared by the instructor, and create a new database """
# pylint: disable=duplicate-code
# from dotenv import load_dotenv
# load_dotenv()

import os

import json
import psycopg
from psycopg import OperationalError

# %%
def load_data_jsonl(filename):
    """
    Loads data from a JSONL file. Each line is one JSON object.
    """
    data = []

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

# back up version of the data
applicant_data= load_data_jsonl("/data/llm_extend_applicant_data_run.jsonl")


# %%
# Create connection to system database
def create_system_connection(user, password):
    """Connect to postgres system database"""
    try:
        conn = psycopg.connect(
            dbname="postgres",
            user=user,
            password=password,
            host="localhost"
        )
        conn.autocommit = True
        return conn
    except OperationalError as e:
        print(f"Connection failed: {e}")
        return None

# %%
# created the database gradcafe_db_v2
# system_conn = create_system_connection("postgres", "181818")
# create_database(system_conn, "gradcafe_db_v2")
# system_conn.close() # pylint: disable=no-member

# connection = psycopg.connect(
#     dbname=os.getenv("POSTGRES_DB"),
#     user=os.getenv("POSTGRES_USER"),
#     password=os.getenv("POSTGRES_PASSWORD"),
#     host=os.getenv("DB_HOST", "127.0.0.1"),
#     port=os.getenv("DB_PORT", "5432"),
# )
connection = psycopg.connect(os.getenv("DATABASE_URL"))

# %%
def execute_query(db_connection, query):
    """this function execute query"""
    db_connection.autocommit = True
    cursor = db_connection.cursor()
    try:
        cursor.execute(query)
        # print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")

# %% [markdown]
# #### insert records

# %%
def format_text(value):
    """
    The current value: 
    1.if the value is None,it returns "Null"
    2. replace ' with '' (SQL needs it)
    3. the whole thing quoted with ' ' (SQL needs it)
    """
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def format_float(value):
    """
    1.if the value is None,it returns "Null"
    2. extract float from json, then convert to string for SQL insertion
    """
    if value is None or value == "":
        return "NULL"
    return str(float(value))

def insert_applicants(db_connection, applicant_data1):
    """Insert applicant rows into the applicants table without duplicating URLs."""
    inserted_count = 0

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

    cur = db_connection.cursor()

    for applicant in applicant_data1:
        row = {
            "program": applicant.get("program"),
            "comments": applicant.get("comments"),
            "date_added": applicant.get("date_added"),
            "url": applicant.get("url"),
            "status": applicant.get("status"),
            "term": applicant.get("term"),
            "us_or_international": applicant.get("US/International"),
            "gpa": applicant.get("GPA") or None,
            "gre": applicant.get("GRE") or None,
            "gre_v": applicant.get("GRE V") or None,
            "gre_aw": applicant.get("GRE AW") or None,
            "degree": applicant.get("Degree"),
            "llm_generated_program": applicant.get("llm-generated-program"),
            "llm_generated_university": applicant.get("llm-generated-university"),
        }

        cur.execute(insert_sql, row)

        if cur.rowcount == 1:
            inserted_count += 1

    db_connection.commit()
    cur.close()

    return inserted_count

# insert_applicants(connection, applicant_data)
INSERTED_APPLICANT_COUNT = insert_applicants(connection, applicant_data)
print(f"Inserted {INSERTED_APPLICANT_COUNT} new applicants.")

# ingestion_watermarks
watermark_cursor = connection.cursor()
watermark_cursor.execute(
    """
    INSERT INTO ingestion_watermarks (source, last_seen, updated_at)
    VALUES (%s, %s, now())
    ON CONFLICT (source)
    DO UPDATE SET
        last_seen = EXCLUDED.last_seen,
        updated_at = now();
    """,
    (
        "llm_extend_applicant_data_run.jsonl",
        applicant_data[-1].get("url") if applicant_data else None,
    ),
)
connection.commit()
watermark_cursor.close()
