# %%
# This notebook use the jsonl data shared by the instructor, and create a new database

# %%

import json
import time

import psycopg
from psycopg import OperationalError

# %%
# def load_data(filename):
#     """
#     Loads cleaned data from a JSON file.
#     """
#     with open(filename, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     return data

# %%
# directory = '/Users/jennifer/Documents/software_concept_python_class/jhu_software_concepts/Module_2/'

# applicant_data= load_data(directory+ "applicant_data_v2.json")
# len(applicant_data)

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
applicant_data= load_data_jsonl("llm_extend_applicant_data_run.jsonl")
len(applicant_data)

# %%
type(applicant_data)

# %%
# inspect the data

print(applicant_data[0])


# %%
print(applicant_data[0].keys()) 

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
# Create new database
def create_database(conn, db_name):
    """Create a new database"""
    try:
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE {db_name};")
        cur.close()
        print(f"Database '{db_name}' created successfully")
    except OperationalError as e:
        print(f"Database creation failed: {e}")

# %%
# created the database gradcafe_db_v2

system_conn = create_system_connection("postgres", "181818")
create_database(system_conn, "gradcafe_db_v2")
system_conn.close()

# %%
def create_db_connection(db_name, db_user, db_password, db_host, db_port):

    """
    create conenction to my db
    """

    connection = None
    try:
        connection = psycopg.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection

# %%
connection = create_db_connection("gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432")

# %%
def execute_query(connection, query):
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        # print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")

# %% [markdown]
# #### create table

# %%
create_users_table = """
CREATE TABLE IF NOT EXISTS applicants (
p_id SERIAL PRIMARY KEY,
program	TEXT,
comments TEXT,
date_added date,
url	TEXT,
status TEXT,
term TEXT,
us_or_international	TEXT,
gpa	FLOAT,
gre	FLOAT,
gre_v FLOAT,
gre_aw FLOAT,
degree TEXT,
llm_generated_program TEXT,
llm_generated_university TEXT
)
"""

execute_query(connection, create_users_table)

# %% [markdown]
# #### insert records

# %%
# check datatype of the json data file
for key, value in applicant_data[0].items():
    print(key, type(value))

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


# def create_program(applicant):
#     university = applicant.get("llm-generated-university")
#     program_name = applicant.get("llm-generated-program")

#     if university is None and program_name is None:
#         return "NULL"

#     if university is None:
#         full_program = program_name
#     elif program_name is None:
#         full_program = university
#     else:
#         full_program = program_name + ", " + university

#     return format_text(full_program)


def insert_applicants(connection, applicant_data):
    for applicant in applicant_data:
        insert_query = f"""
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
            {format_text(applicant.get("program"))},
            {format_text(applicant.get("comments"))},
            {format_text(applicant.get("date_added"))},
            {format_text(applicant.get("url"))},
            {format_text(applicant.get("status"))},
            {format_text(applicant.get("term"))},
            {format_text(applicant.get("US/International"))},
            {format_float(applicant.get("GPA"))},
            {format_float(applicant.get("GRE"))},
            {format_float(applicant.get("GRE V"))},
            {format_float(applicant.get("GRE AW"))},
            {format_text(applicant.get("Degree"))},
            {format_text(applicant.get("llm-generated-program"))},
            {format_text(applicant.get("llm-generated-university"))}
        );
        """

        execute_query(connection, insert_query)


insert_applicants(connection, applicant_data)

# %% [markdown]
# #### test connection and Read query 

# %%
# Note: the two functions are different: 
# execute_query ---- runs query, does not fetch data
# execute_read_query ---- runs SELECT query, fetches and returns data

def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except OperationalError as e:
        print(f"The error '{e}' occurred")


select_applicants = "SELECT * FROM applicants limit 10"
applicants = execute_read_query(connection, select_applicants)

for applicant in applicants:
    print(applicant)

# %%
total_applicants = "SELECT count(*) FROM applicants"
tot = execute_read_query(connection, total_applicants)
print(tot)


