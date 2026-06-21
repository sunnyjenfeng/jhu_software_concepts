""" This module connect to PostgreSQL DB and execute query"""
# pylint: disable=duplicate-code

import psycopg
from psycopg import OperationalError

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
# #### Read query

# %%
# Note: the two functions are different:
# execute_query ---- runs query, does not fetch data
# execute_read_query ---- runs SELECT query, fetches and returns data

# def execute_read_query(db_connection, query):
#     """
#     This function runs SELECT query, fetches and returns data
#     """
#     cursor = db_connection.cursor()
#     result = None
#     try:
#         cursor.execute(query)
#         result = cursor.fetchall()
#         return result
#     except OperationalError as e:
#         print(f"The error '{e}' occurred")
#         return None

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

# SELECT_APPLICANTS = "SELECT * FROM applicants limit 10"
# applicants = execute_read_query(connection, SELECT_APPLICANTS)

# for applicant in applicants:
#     print(applicant)

# %% [markdown]
# #### Q1: How many entries do you have in your database who have applied for Fall 2026?

# %%
# first check why type of data in term
QUERY1A = "SELECT distinct term FROM applicants"
query1a_output = execute_read_query(connection, QUERY1A)
print(query1a_output)

# %%
QUERY1 = "SELECT count(*) FROM applicants where term = 'Fall 2026'"
query1_output = execute_read_query(connection, QUERY1)
print(query1_output)

# %% [markdown]
# #### Q2: What percentage of entries are from international students (not American or Other)
# (to two decimal places)?

# %%
# use triple quoted string for nice layout query!
QUERY2 = """
SELECT
    ROUND(100.0 * SUM(CASE WHEN us_or_international = 'International' THEN 1
                           ELSE 0
                      END
                      ) / COUNT(*),
        2
    ) AS international_pct
FROM applicants;
"""

query2_output = execute_read_query(connection, QUERY2)
print(query2_output)

# %%
# double check query2 results
QUERY2_CHECK = """
SELECT distinct us_or_international, count(*)
from applicants
group by us_or_international;
"""

query2_chk_output = execute_read_query(connection, QUERY2_CHECK)
print(query2_chk_output)



# %% [markdown]
# #### Q3: What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?

# %%
# query3 = """
# SELECT
#     ROUND(AVG(gpa), 2) AS avg_gpa,
#     ROUND(AVG(gre), 2) AS avg_gre,
#     ROUND(AVG(gre_v),2) AS avg_gre_v,
#     ROUND(AVG(gre_aw),2) AS avg_gre_aw
# FROM applicants;
# """
QUERY3 = """
SELECT
    ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
    ROUND(AVG(gre)::numeric, 2) AS avg_gre,
    ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
    ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
FROM applicants;
"""

query3_output = execute_read_query(connection, QUERY3)
print(query3_output)

# %%

avg_gpa, avg_gre, avg_gre_v, avg_gre_aw = query3_output[0]

print("Average GPA:", avg_gpa)
print("Average GRE:", avg_gre)
print("Average GRE V:", avg_gre_v)
print("Average GRE AW:", avg_gre_aw)

# %% [markdown]
# #### Q4: What is their average GPA of American students in Fall 2026?

# %%
QUERY4 = """
SELECT
    ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
FROM applicants
where us_or_international = 'American' and term = 'Fall 2026';
"""

query4_output = execute_read_query(connection, QUERY4)
print(query4_output)

# %% [markdown]
# #### Q5: What percent of entries for Fall 2026 are Acceptances (to two decimal places)?

# %%
QUERY5A = """
SELECT
   distinct status
FROM applicants
where term = 'Fall 2026'
limit 5;
"""

query5a_output = execute_read_query(connection, QUERY5A)
print(query5a_output)

# %%
QUERY5 = """
SELECT
    ROUND(
        100.0 * SUM(
            CASE WHEN status ILIKE '%Accepted%' THEN 1
                 ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS fall_2026_accept_pct
FROM applicants
WHERE term = 'Fall 2026';
"""

query5_output = execute_read_query(connection, QUERY5)
print(query5_output)

# %% [markdown]
# #### Q6:What is the average GPA of applicants who applied for Fall 2026 who are Acceptances?

# %%
QUERY6 = """
SELECT
   avg(gpa)
FROM applicants
where term = 'Fall 2026' and status ILIKE '%Accepted%';
"""

query6_output = execute_read_query(connection, QUERY6)
print(query6_output)

# %% [markdown]
# #### Q7: How many entries are from applicants who applied to JHU for a masters degrees
# in Computer Science?

# %%
QUERY7A = """
SELECT
   distinct degree
FROM applicants;
"""

query7a_output = execute_read_query(connection, QUERY7A)
print(query7a_output)

# %%
# this test print the records found
QUERY7B = """
SELECT *
FROM applicants
WHERE degree = 'Masters'
  AND (
      "llm_generated_university" ILIKE '%Johns Hopkins%'
      OR "llm_generated_university" ILIKE '%John Hopkins%'
      OR "llm_generated_university" ILIKE '%JHU%'
  )
  AND "llm_generated_program" ILIKE '%computer science%'
  limit 5;
"""

query7b_output = execute_read_query(connection, QUERY7B)
print(query7b_output)

# %%
QUERY7 = """
SELECT count(*)
FROM applicants
WHERE degree = 'Masters'
  AND (
      program ILIKE '%Johns Hopkins%'
      OR program ILIKE '%John Hopkins%'
      OR program ILIKE '%JHU%'
  )
  AND program ILIKE '%computer science%';
"""
# ILIKE is case insensitive
query7_output = execute_read_query(connection, QUERY7)
print(query7_output)

# %% [markdown]
# #### Q8: How many entries from 2026 are acceptances from applicants who applied to
# Georgetown University, MIT, Stanford University, or Carnegie Mellon University for
# a PhD in Computer Science?

# %%
# query8 = """
# SELECT COUNT(*)
# FROM applicants
# WHERE status = 'Accepted'
#   AND degree = 'PhD'
#   AND llm_generated_program ILIKE '%computer science%'
#   AND EXTRACT(YEAR FROM date_added) = 2026
#   AND (
#       llm_generated_university = 'Georgetown University'
#       OR llm_generated_university = 'Stanford University'
#       OR llm_generated_university = 'Carnegie Mellon University'
#       OR llm_generated_university = 'Massachusetts Institute of Technology'
#       OR llm_generated_university = 'MIT'
#   );
# """

QUERY8 = """
SELECT COUNT(*)
FROM applicants
WHERE status = 'Accepted'
  AND degree = 'PhD'
  AND program ILIKE '%computer science%'
  AND EXTRACT(YEAR FROM date_added) = 2026
  AND (
      program ILIKE '%Georgetown%'
      OR program ILIKE '%Stanford%'
      OR program ILIKE '%Carnegie Mellon%'
      OR program ILIKE '%Massachusetts Institute of Technology%'
      OR program ILIKE '%MIT%'
  );
"""

query8_output = execute_read_query(connection, QUERY8)
print(query8_output)

# %% [markdown]
# #### Q9: Do you numbers for question 8 change if you use LLM Generated Fields
# (rather than your downloaded fields)?

# %%
QUERY9 = """
SELECT COUNT(*)
FROM applicants
WHERE status = 'Accepted'
  AND degree = 'PhD'
  AND llm_generated_program ILIKE '%computer science%'
  AND EXTRACT(YEAR FROM date_added) = 2026
  AND (
      llm_generated_university ILIKE '%Georgetown%'
      OR llm_generated_university ILIKE '%Stanford%'
      OR llm_generated_university ILIKE '%Carnegie Mellon%'
      OR llm_generated_university ILIKE '%Massachusetts Institute of Technology%'
      OR llm_generated_university ILIKE '%MIT%'
  );
"""

query9_output = execute_read_query(connection, QUERY9)
print(query9_output)

# %% [markdown]
# #### Q10: How many entries for students applied for Fall 2026 term for Stanford Univerity
# Masters program per acceptance status?

# %%
QUERY10 = """
SELECT
    CASE
        WHEN status ILIKE 'Accepted%' THEN 'Accepted'
        WHEN status ILIKE 'Rejected%' THEN 'Rejected'
        WHEN status ILIKE 'Wait listed%' THEN 'Waitlisted'
        WHEN status ILIKE 'Interview%' THEN 'Interview'
        ELSE status
    END AS acceptance_status,
    COUNT(*) AS num_entries
FROM applicants
WHERE term = 'Fall 2026'
  AND degree = 'Masters'
  AND llm_generated_university ILIKE '%Stanford%'
GROUP BY acceptance_status
ORDER BY num_entries DESC;
"""

query10_output = execute_read_query(connection, QUERY10)
print(query10_output)

# %% [markdown]
# #### Q11: For students applied for Fall 2026 term for Stanford Univerity Masters program
# and got accepted, what is the percentage of international student?

# %%
QUERY11 = """
SELECT
    ROUND(
        100.0 * SUM(
            CASE WHEN us_or_international = 'International' THEN 1
                 ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS international_student_percent
FROM applicants
WHERE term = 'Fall 2026'
  AND degree = 'Masters'
  AND llm_generated_university ILIKE '%Stanford%'
  AND status ILIKE 'Accepted%';
"""

query11_output = execute_read_query(connection, QUERY11)

print(query11_output)
