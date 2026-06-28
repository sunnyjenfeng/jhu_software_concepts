"""Parameterized queries for the Flask analysis page."""
# pylint: disable=duplicate-code

from psycopg import sql

MAX_LIMIT = 100


def clamp_limit(limit):
    """Keep limit between 1 and MAX_LIMIT."""
    return max(1, min(int(limit), MAX_LIMIT))


QUERIES = [
    {
        "number": 1,
        "question": "How many entries do you have in your database who have applied for Fall 2026?",
        "sql": sql.SQL("""
            SELECT COUNT(*)
            FROM {table}
            WHERE {term} = %s
            LIMIT %s;
        """).format(
            table=sql.Identifier("applicants"),
            term=sql.Identifier("term"),
        ),
        "params": ["Fall 2026", clamp_limit(1)],
    },
    {
        "number": 2,
        "question": "What percentage of entries are from international students (not American or"
        "Other) (to two decimal places)?",
        "sql": sql.SQL("""
            SELECT ROUND(
                100.0 * SUM(
                    CASE WHEN {us_or_international} = %s THEN 1 ELSE 0 END
                ) / COUNT(*),
                2
            ) AS international_pct
            FROM {table}
            LIMIT %s;
        """).format(
            us_or_international=sql.Identifier("us_or_international"),
            table=sql.Identifier("applicants"),
        ),
        "params": ["International", clamp_limit(1)],
    },
    {
        "number": 3,
        "question": "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these"
        "metrics?",
        "sql": sql.SQL("""
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
            table=sql.Identifier("applicants"),
        ),
        "params": [clamp_limit(1)],
    },
    {
        "number": 4,
        "question": "What is their average GPA of American students in Fall 2026?",
        "sql": sql.SQL("""
            SELECT ROUND(AVG({gpa})::numeric, 2) AS avg_gpa
            FROM {table}
            WHERE {us_or_international} = %s
              AND {term} = %s
            LIMIT %s;
        """).format(
            gpa=sql.Identifier("gpa"),
            table=sql.Identifier("applicants"),
            us_or_international=sql.Identifier("us_or_international"),
            term=sql.Identifier("term"),
        ),
        "params": ["American", "Fall 2026", clamp_limit(1)],
    },
    {
        "number": 5,
        "question": "What percent of entries for Fall 2026 are Acceptances (to two decimal "
        "places)?",
        "sql": sql.SQL("""
            SELECT
                ROUND(
                    100.0 * SUM(
                        CASE WHEN {status} ILIKE %s THEN 1 ELSE 0 END
                    ) / COUNT(*),
                    2
                ) AS fall_2026_accept_pct
            FROM {table}
            WHERE {term} = %s
            LIMIT %s;
        """).format(
            status=sql.Identifier("status"),
            table=sql.Identifier("applicants"),
            term=sql.Identifier("term"),
        ),
        "params": ["%Accepted%", "Fall 2026", clamp_limit(1)],
    },
    {
        "number": 6,
        "question": "What is the average GPA of applicants who applied for Fall 2026 who are"
        "Acceptances?",
        "sql": sql.SQL("""
            SELECT ROUND(AVG({gpa})::numeric, 2)
            FROM {table}
            WHERE {term} = %s
              AND {status} ILIKE %s
            LIMIT %s;
        """).format(
            gpa=sql.Identifier("gpa"),
            table=sql.Identifier("applicants"),
            term=sql.Identifier("term"),
            status=sql.Identifier("status"),
        ),
        "params": ["Fall 2026", "%Accepted%", clamp_limit(1)],
    },
    {
        "number": 7,
        "question": "How many entries are from applicants who applied to JHU for a masters degrees"
        "in Computer Science?",
        "sql": sql.SQL("""
            SELECT COUNT(*)
            FROM {table}
            WHERE {degree} = %s
              AND (
                  {program} ILIKE %s
                  OR {program} ILIKE %s
                  OR {program} ILIKE %s
              )
              AND {program} ILIKE %s
            LIMIT %s;
        """).format(
            table=sql.Identifier("applicants"),
            degree=sql.Identifier("degree"),
            program=sql.Identifier("program"),
        ),
        "params": [
            "Masters",
            "%Johns Hopkins%",
            "%John Hopkins%",
            "%JHU%",
            "%computer science%",
            clamp_limit(1),
        ],
    },
    {
        "number": 8,
        "question": "How many entries from 2026 are acceptances from applicants who applied to "
        "Georgetown University, MIT, Stanford University, or Carnegie Mellon University for a PhD "
        "in Computer Science?",
        "sql": sql.SQL("""
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
            table=sql.Identifier("applicants"),
            status=sql.Identifier("status"),
            degree=sql.Identifier("degree"),
            program=sql.Identifier("program"),
            date_added=sql.Identifier("date_added"),
        ),
        "params": [
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
    },
    {
        "number": 9,
        "question": "Same as Q8, using LLM-generated program and university fields.",
        "sql": sql.SQL("""
            SELECT COUNT(*) AS entries
            FROM {table}
            WHERE {status} ILIKE %s
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
            llm_generated_university=sql.Identifier("llm_generated_university"),
        ),
        "params": [
            "Accepted%",
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
    },
    {
        "number": 10,
        "question": "How many entries for students applied for Fall 2026 term for"
        "Stanford Univerity"
        "Masters program per acceptance status? ",
        "sql": sql.SQL("""
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
            llm_generated_university=sql.Identifier("llm_generated_university"),
        ),
        "params": [
            "Accepted%",
            "Accepted",
            "Rejected%",
            "Rejected",
            "Wait listed%",
            "Waitlisted",
            "Interview%",
            "Interview",
            "Fall 2026",
            "Masters",
            "%Stanford%",
            clamp_limit(100),
        ],
    },
    {
        "number": 11,
        "question": "For students applied for Fall 2026 term for Stanford Univerity Masters program"
        "and got accepted, what is the percentage of international student?",
        "sql": sql.SQL("""
            SELECT
                ROUND(
                    100.0 * SUM(
                        CASE WHEN {us_or_international} = %s THEN 1 ELSE 0 END
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
            status=sql.Identifier("status"),
        ),
        "params": [
            "International",
            "Fall 2026",
            "Masters",
            "%Stanford%",
            "Accepted%",
            clamp_limit(1),
        ],
    },
]
