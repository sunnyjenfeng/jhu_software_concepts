QUERIES = [
    {
        "number": 1,
        "title": "Fall 2026 Applications",
        "question": "How many entries applied for the Fall 2026 term?",
        "sql": """
            SELECT COUNT(*) AS entries
            FROM applicants
            WHERE term = 'Fall 2026';
        """,
        "type": "metric",
        "suffix": "entries",
    },
    {
        "number": 2,
        "title": "International Share",
        "question": "What percentage of all entries are international students?",
        "sql": """
            SELECT ROUND(
                100.0 * SUM(CASE WHEN us_or_international = 'International' THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS international_pct
            FROM applicants;
        """,
        "type": "metric",
        "suffix": "%",
    },
    {
        "number": 3,
        "title": "Average Scores",
        "question": "What are the average GPA, GRE, GRE V, and GRE AW values?",
        "sql": """
            SELECT
                ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
                ROUND(AVG(gre)::numeric, 2) AS avg_gre,
                ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
                ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
            FROM applicants;
        """,
        "type": "table",
    },
    {
        "number": 4,
        "title": "American Fall 2026 GPA",
        "question": "What is the average GPA of American students in Fall 2026?",
        "sql": """
            SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
            FROM applicants
            WHERE us_or_international = 'American'
              AND term = 'Fall 2026';
        """,
        "type": "metric",
        "suffix": "avg GPA",
    },
    {
        "number": 5,
        "title": "Fall 2026 Acceptance Rate",
        "question": "What percent of Fall 2026 entries are acceptances?",
        "sql": """
            SELECT ROUND(
                100.0 * SUM(CASE WHEN status ILIKE 'Accepted%' THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS fall_2026_accept_pct
            FROM applicants
            WHERE term = 'Fall 2026';
        """,
        "type": "metric",
        "suffix": "%",
    },
    {
        "number": 6,
        "title": "Accepted Fall 2026 GPA",
        "question": "What is the average GPA of accepted Fall 2026 applicants?",
        "sql": """
            SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
            FROM applicants
            WHERE term = 'Fall 2026'
              AND status ILIKE 'Accepted%';
        """,
        "type": "metric",
        "suffix": "avg GPA",
    },
    {
        "number": 7,
        "title": "JHU CS Masters",
        "question": "How many entries applied to JHU for a Masters in Computer Science?",
        "sql": """
            SELECT COUNT(*) AS entries
            FROM applicants
            WHERE degree = 'Masters'
              AND (
                  llm_generated_university ILIKE '%Johns Hopkins%'
                  OR llm_generated_university ILIKE '%John Hopkins%'
                  OR llm_generated_university ILIKE '%JHU%'
              )
              AND llm_generated_program ILIKE '%computer science%';
        """,
        "type": "metric",
        "suffix": "entries",
    },
    {
        "number": 8,
        "title": "Selected CS PhD Acceptances",
        "question": "2026 acceptances to Georgetown, MIT, Stanford, or Carnegie Mellon for a CS PhD using downloaded fields.",
        "sql": """
            SELECT COUNT(*) AS entries
            FROM applicants
            WHERE status ILIKE 'Accepted%'
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
        "type": "metric",
        "suffix": "entries",
    },
    {
        "number": 9,
        "title": "Selected CS PhD Acceptances, LLM Fields",
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
        "type": "metric",
        "suffix": "entries",
    },
    {
        "number": 10,
        "title": "Stanford Masters Status",
        "question": "Fall 2026 Stanford University Masters entries per acceptance status.",
        "sql": """
            SELECT
                CASE
                    WHEN status ILIKE 'Accepted%' THEN 'Accepted'
                    WHEN status ILIKE 'Rejected%' THEN 'Rejected'
                    WHEN status ILIKE 'Waitlisted%' OR status ILIKE 'Wait listed%' THEN 'Waitlisted'
                    WHEN status ILIKE 'Interview%' THEN 'Interview'
                    ELSE COALESCE(status, 'Unknown')
                END AS acceptance_status,
                COUNT(*) AS num_entries
            FROM applicants
            WHERE term = 'Fall 2026'
              AND degree = 'Masters'
              AND llm_generated_university ILIKE '%Stanford%'
            GROUP BY acceptance_status
            ORDER BY num_entries DESC;
        """,
        "type": "table",
    },
    {
        "number": 11,
        "title": "Stanford Accepted International Share",
        "question": "Percent international among accepted Fall 2026 Stanford University Masters entries.",
        "sql": """
            SELECT ROUND(
                100.0 * SUM(CASE WHEN us_or_international = 'International' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
                2
            ) AS international_student_percent
            FROM applicants
            WHERE term = 'Fall 2026'
              AND degree = 'Masters'
              AND llm_generated_university ILIKE '%Stanford%'
              AND status ILIKE 'Accepted%';
        """,
        "type": "metric",
        "suffix": "%",
    },
]
