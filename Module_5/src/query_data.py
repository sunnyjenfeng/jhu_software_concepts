# %%
""" This module connect to PostgreSQL DB and execute query"""
# pylint: disable=duplicate-code

import psycopg
from psycopg import OperationalError, sql

# %%
def create_db_connection(db_name, db_user, db_password, db_host, db_port):

    """
    create conenction to my db
    """
    db_connection = None
    try:
        db_connection = psycopg.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return db_connection


# %%
connection = create_db_connection("gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432")


# %%
def execute_query(db_connection, query):
    """
    This function execute query. But it does not fetch data
    """
    db_connection.autocommit = True
    cursor = db_connection.cursor()
    try:
        cursor.execute(query)
        # print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")


# %% [markdown]
#  #### Read query

# %%
MAX_LIMIT = 100

def clamp_limit(limit):
    """Keep limit between 1 and MAX_LIMIT."""
    return max(1, min(int(limit), MAX_LIMIT))

def execute_read_query(db_connection, stmt, params=None):
    """
    Refactored version
    This function runs SELECT query, fetches and returns data
    """
    cursor = db_connection.cursor()
    try:
        cursor.execute(stmt, params or [])
        return cursor.fetchall()
    except OperationalError as error:
        print(f"The error '{error}' occurred")
        return None


# %% [markdown]
#  #### Q1: How many entries do you have in your database who have applied for Fall 2026?

# %%
QUERY1 = sql.SQL("""
SELECT count(*)
FROM {table}
WHERE {term} = %s
LIMIT %s;
""").format(
    table=sql.Identifier("applicants"),
    term=sql.Identifier("term")
)

query1_output = execute_read_query(connection, QUERY1, ["Fall 2026", clamp_limit(1)])
print(query1_output)

# %%
connection.rollback()

# %% [markdown]
#  #### Q2: What percentage of entries are from international students (not American or Other)
# 
#  (to two decimal places)?

# %%

QUERY2 = sql.SQL("""
SELECT
    ROUND(
        100.0 * SUM(
            CASE WHEN {us_or_international} = %s THEN 1
                 ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS international_pct
FROM {table}
LIMIT %s;
""").format(
    us_or_international=sql.Identifier("us_or_international"),
    table=sql.Identifier("applicants")
)

query2_output = execute_read_query(
    connection,
    QUERY2,
    ["International", clamp_limit(1)]
)

print(query2_output)


# %%
# # double check query2 results
# QUERY2_CHECK = """
# SELECT distinct us_or_international, count(*)
# from applicants
# group by us_or_international;
# """

# query2_chk_output = execute_read_query(connection, QUERY2_CHECK)
# print(query2_chk_output)


# %% [markdown]
#  #### Q3: What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?

# %%
QUERY3 = sql.SQL("""
SELECT
    ROUND(AVG({gpa})::numeric, 2) AS avg_gpa,
    ROUND(AVG({gre})::numeric, 2) AS avg_gre,
    ROUND(AVG({gre_v})::numeric, 2) AS avg_gre_v,
    ROUND(AVG({gre_aw})::numeric, 2) AS avg_gre_aw
FROM {table}
LIMIT %s;
""").format(
    gpa=sql.Identifier("gpa"),
    gre=sql.Identifier("gre"),
    gre_v=sql.Identifier("gre_v"),
    gre_aw=sql.Identifier("gre_aw"),
    table=sql.Identifier("applicants")
)
# Query3 has no filter, so the only parameter is the limit.
query3_output = execute_read_query(connection, QUERY3, [clamp_limit(1)])
print(query3_output)


# %%

avg_gpa, avg_gre, avg_gre_v, avg_gre_aw = query3_output[0]

print("Average GPA:", avg_gpa)
print("Average GRE:", avg_gre)
print("Average GRE V:", avg_gre_v)
print("Average GRE AW:", avg_gre_aw)


# %% [markdown]
#  #### Q4: What is their average GPA of American students in Fall 2026?

# %%
QUERY4 = sql.SQL("""
SELECT
    ROUND(AVG({gpa})::numeric, 2) AS avg_gpa
FROM {table}
where {us_or_international} = %s and term = %s
LIMIT %s;
""").format(
    gpa=sql.Identifier("gpa"),
    us_or_international=sql.Identifier("us_or_international"),
    term=sql.Identifier("term"),
    table=sql.Identifier("applicants")
    )

query4_output = execute_read_query(connection, QUERY4, ["American", 'Fall 2026', clamp_limit(1)])
print(query4_output)


# %%
connection.rollback()

# %% [markdown]
#  #### Q5: What percent of entries for Fall 2026 are Acceptances (to two decimal places)?

# %%
QUERY5 = sql.SQL("""
SELECT
    ROUND(
        100.0 * SUM(
            CASE WHEN {status} ILIKE %s THEN 1
                 ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS fall_2026_accept_pct
FROM {table}
WHERE {term} = %s
LIMIT %s;
""").format(
    status=sql.Identifier("status"),
    term=sql.Identifier("term"),
    table=sql.Identifier("applicants")
    )

query5_output = execute_read_query(connection, QUERY5, ['%Accepted%','Fall 2026', clamp_limit(1)])
print(query5_output)


# %% [markdown]
#  #### Q6:What is the average GPA of applicants who applied for Fall 2026 who are Acceptances?

# %%
QUERY6 = sql.SQL("""
SELECT
   ROUND(AVG({gpa})::numeric, 2)
FROM {table}
where {term} = %s and {status} ILIKE %s
LIMIT %s;
""").format(
    gpa=sql.Identifier("gpa"),
    term=sql.Identifier("term"),
    status=sql.Identifier("status"),
    table=sql.Identifier("applicants")
    )

query6_output = execute_read_query(connection, QUERY6, ['Fall 2026', '%Accepted%', clamp_limit(1)])
print(query6_output)


# %% [markdown]
#  #### Q7: How many entries are from applicants who applied to JHU for a masters degrees
# 
#  in Computer Science?

# %%
QUERY7 = sql.SQL("""
SELECT count(*)
FROM {table}
WHERE {degree} = %s
  AND (
      {program} ILIKE %s
      OR {program} ILIKE %s
  )
  AND {program} ILIKE %s
LIMIT %s;
""").format(
    degree=sql.Identifier("degree"),
    program=sql.Identifier("program"),
    table=sql.Identifier("applicants")
    )
# ILIKE is case insensitive
query7_output = execute_read_query(
connection, QUERY7, ['Masters', '%Johns Hopkins%', '%JHU%','%computer science%', clamp_limit(1)])
print(query7_output)


# %% [markdown]
#  #### Q8: How many entries from 2026 are acceptances from applicants who applied to
# 
#  Georgetown University, MIT, Stanford University, or Carnegie Mellon University for
# 
#  a PhD in Computer Science?

# %%
QUERY8 = sql.SQL("""
SELECT COUNT(*)
FROM {table}
WHERE {status} = %s
  AND {degree} = %s
  AND {program} ILIKE %s
  AND EXTRACT(YEAR FROM {date_added}) = %s
  AND (
      {program} ILIKE %s
      OR {program} ILIKE %s
      OR {program} ILIKE %s
      OR {program} ILIKE %s
      OR {program} ILIKE %s
  )
LIMIT %s;
""").format(
    status=sql.Identifier("status"),
    degree=sql.Identifier("degree"),
    program=sql.Identifier("program"),
    date_added=sql.Identifier("date_added"),
    table=sql.Identifier("applicants")
    )

query8_output = execute_read_query(connection, QUERY8, 
['Accepted','PhD', '%computer science%', 2026, '%Georgetown%', 
'%Stanford%','%Carnegie Mellon%', '%Massachusetts Institute of Technology%', '%MIT%', 
clamp_limit(1)])
print(query8_output)


# %% [markdown]
#  #### Q9: Do you numbers for question 8 change if you use LLM Generated Fields
# 
#  (rather than your downloaded fields)?

# %%
QUERY9 = sql.SQL("""
SELECT COUNT(*)
FROM {table}
WHERE {status} = %s
  AND {degree} = %s
  AND {llm_generated_program} ILIKE %s
  AND EXTRACT(YEAR FROM {date_added}) = %s
  AND (
      {llm_generated_university} ILIKE %s
      OR {llm_generated_university} ILIKE %s
      OR {llm_generated_university} ILIKE %s
      OR {llm_generated_university} ILIKE %s
      OR {llm_generated_university} ILIKE %s
  )
LIMIT %s;
""").format(
    table=sql.Identifier("applicants"),
    status=sql.Identifier("status"),
    degree=sql.Identifier("degree"),
    llm_generated_program=sql.Identifier("llm_generated_program"),
    date_added=sql.Identifier("date_added"),
    llm_generated_university=sql.Identifier("llm_generated_university")
)

query9_output = execute_read_query(
    connection,
    QUERY9,
    [
        "Accepted",
        "PhD",
        "%computer science%",
        2026,
        "%Georgetown%",
        "%Stanford%",
        "%Carnegie Mellon%",
        "%Massachusetts Institute of Technology%",
        "%MIT%",
        clamp_limit(1),
    ],
)

print(query9_output)


# %% [markdown]
#  #### Q10: How many entries for students applied for Fall 2026 term for Stanford Univerity
# 
#  Masters program per acceptance status?

# %%
QUERY10 = sql.SQL("""
SELECT
    CASE
        WHEN {status} ILIKE %s THEN %s
        WHEN {status} ILIKE %s THEN %s
        WHEN {status} ILIKE %s THEN %s
        WHEN {status} ILIKE %s THEN %s
        ELSE {status}
    END AS acceptance_status,
    COUNT(*) AS num_entries
FROM {table}
WHERE {term} = %s
  AND {degree} = %s
  AND {llm_generated_university} ILIKE %s
GROUP BY acceptance_status
ORDER BY num_entries DESC
LIMIT %s;
""").format(
    status=sql.Identifier("status"),
    table=sql.Identifier("applicants"),
    term=sql.Identifier("term"),
    degree=sql.Identifier("degree"),
    llm_generated_university=sql.Identifier("llm_generated_university")
)

query10_output = execute_read_query(
    connection,
    QUERY10,
    [
        "Accepted%", "Accepted",
        "Rejected%", "Rejected",
        "Wait listed%", "Waitlisted",
        "Interview%", "Interview",
        "Fall 2026",
        "Masters",
        "%Stanford%",
        clamp_limit(100),
    ],
)

print(query10_output)

# %% [markdown]
#  #### Q11: For students applied for Fall 2026 term for Stanford Univerity Masters program
# 
#  and got accepted, what is the percentage of international student?

# %%
QUERY11 = sql.SQL("""
SELECT
    ROUND(
        100.0 * SUM(
            CASE WHEN {us_or_international} = %s THEN 1
                 ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS international_student_percent
FROM {table}
WHERE {term} = %s
  AND {degree} = %s
  AND {llm_generated_university} ILIKE %s
  AND {status} ILIKE %s
LIMIT %s;
""").format(
    us_or_international=sql.Identifier("us_or_international"),
    table=sql.Identifier("applicants"),
    term=sql.Identifier("term"),
    degree=sql.Identifier("degree"),
    llm_generated_university=sql.Identifier("llm_generated_university"),
    status=sql.Identifier("status")
)

query11_output = execute_read_query(
    connection,
    QUERY11,
    [
        "International",
        "Fall 2026",
        "Masters",
        "%Stanford%",
        "Accepted%",
        clamp_limit(1),
    ],
)

print(query11_output)


