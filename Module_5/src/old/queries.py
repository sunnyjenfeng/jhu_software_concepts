"""This module list all the queries and results to shown on the Flask webpage"""
# pylint: disable=duplicate-code

QUERIES = [
    {
        "number": 1,
        "question": "How many entries do you have in your database who have applied for Fall 2026?",
        "sql": """
         SELECT count(*) 
         FROM applicants 
         WHERE term = 'Fall 2026'
        """,
    },
    {
        "number": 2,
        "question": "What percentage of entries are from international students (not American or" 
        "Other) (to two decimal places)?",
        "sql": """
            SELECT ROUND(
                100.0 * SUM(CASE WHEN us_or_international = 'International' THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS international_pct
            FROM applicants;
        """,
    },
    {
        "number": 3,
        "question": "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these" 
        "metrics?",
        "sql": """
            SELECT
                ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
                ROUND(AVG(gre)::numeric, 2) AS avg_gre,
                ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
                ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
            FROM applicants;
        """,
    },
    {
        "number": 4,
        "question": "What is their average GPA of American students in Fall 2026?",
        "sql": """
            SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
            FROM applicants
            WHERE us_or_international = 'American'
              AND term = 'Fall 2026';
        """,
    },
    {
        "number": 5,
        "question": "What percent of entries for Fall 2026 are Acceptances (to two decimal "
        "places)?",
        "sql": """
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
        """,
    },
    {
        "number": 6,
        "question": "What is the average GPA of applicants who applied for Fall 2026 who are" 
        "Acceptances?",
        "sql": """
            SELECT
                 ROUND(AVG(gpa)::numeric, 2)
            FROM applicants
            where term = 'Fall 2026' and status ILIKE '%Accepted%';
        """,
    },
    {
        "number": 7,
        "question": "How many entries are from applicants who applied to JHU for a masters degrees" 
        "in Computer Science?",
        "sql": """
           SELECT count(*)
           FROM applicants
           WHERE degree = 'Masters'
            AND (
                program ILIKE '%Johns Hopkins%'
                OR program ILIKE '%John Hopkins%'
                OR program ILIKE '%JHU%'
            )
            AND program ILIKE '%computer science%';
        """,
    },
    {
        "number": 8,
        "question": "How many entries from 2026 are acceptances from applicants who applied to "
        "Georgetown University, MIT, Stanford University, or Carnegie Mellon University for a PhD "
        "in Computer Science?",
        "sql": """
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
        """,
    },
    {
        "number": 9,
        "question": "Same as Q8, using LLM-generated program and university fields.",
        "sql": """
            SELECT COUNT(*) AS entries
            FROM applicants
            WHERE status ILIKE 'Accepted%'
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
        """,
    },
    {
        "number": 10,
        "question": "How many entries for students applied for Fall 2026 term for"
        "Stanford Univerity"
        "Masters program per acceptance status? ",
        "sql": """
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
        """,
    },
    {
        "number": 11,
        "question": "For students applied for Fall 2026 term for Stanford Univerity Masters program"
        "and got accepted, what is the percentage of international student?",
        "sql": """
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
        """,
    },
]
