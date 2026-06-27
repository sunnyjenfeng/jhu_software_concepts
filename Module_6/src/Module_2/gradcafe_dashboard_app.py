"""This module uses Flask to create a gradcafe dashboard"""

import os
from decimal import Decimal

import psycopg
from flask import Flask, render_template_string
from psycopg import OperationalError


app = Flask(__name__)

DB_CONFIG = {
    "dbname": os.getenv("GRADCAFE_DB_NAME", "gradcafe_db_v2"),
    "user": os.getenv("GRADCAFE_DB_USER", "postgres"),
    "password": os.getenv("GRADCAFE_DB_PASSWORD", "181818"),
    "host": os.getenv("GRADCAFE_DB_HOST", "127.0.0.1"),
    "port": os.getenv("GRADCAFE_DB_PORT", "5432"),
}

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
        "question": "2026 acceptances to Georgetown, MIT, Stanford, or Carnegie Mellon "
        "for a CS PhD using downloaded fields.",
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
        "question": "Percent international among accepted Fall 2026 Stanford University"
        "Masters entries.",
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

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GradCafe PostgreSQL Query Results</title>
  <style>
    :root {
      --ink: #17212b;
      --muted: #64748b;
      --line: #d9e2ec;
      --paper: #f7f9fb;
      --panel: #ffffff;
      --accent: #0f766e;
      --accent-soft: #d9f1ec;
      --blue: #2563eb;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      color: var(--ink);
      background: linear-gradient(180deg, #eef6f5 0, var(--paper) 310px), var(--paper);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }

    .shell { width: min(1180px, calc(100% - 32px)); margin: 0 auto; }
    header { padding: 34px 0 22px; }

    .eyebrow {
      color: var(--accent);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    h1 {
      margin: 8px 0;
      font-size: clamp(2rem, 4vw, 3.8rem);
      line-height: 1.03;
      letter-spacing: 0;
    }

    .lede { max-width: 760px; color: #475569; font-size: 1.04rem; margin: 0; }
    .status-bar { display: flex; flex-wrap: wrap; gap: 10px; margin: 24px 0 10px; }

    .pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.78);
      padding: 8px 12px;
      color: #334155;
      font-size: 0.9rem;
      font-weight: 650;
    }

    .error {
      margin: 24px 0;
      border: 1px solid #fecdd3;
      background: #fff1f2;
      color: #9f1239;
      border-radius: 8px;
      padding: 16px;
      font-weight: 650;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
      padding: 18px 0 42px;
    }

    .result-card {
      min-height: 230px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    .result-card.wide { grid-column: span 2; }

    .card-head {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 16px 12px;
      border-bottom: 1px solid #edf2f7;
    }

    .number {
      width: 38px;
      height: 38px;
      display: grid;
      place-items: center;
      flex: 0 0 auto;
      border-radius: 8px;
      background: var(--accent-soft);
      color: #0f5f59;
      font-weight: 850;
    }

    h2 { margin: 0; font-size: 1rem; line-height: 1.25; letter-spacing: 0; }

    .question {
      margin: 0;
      padding: 12px 16px 0;
      color: var(--muted);
      font-size: 0.92rem;
      min-height: 58px;
    }

    .metric {
      margin: auto 16px 18px;
      display: flex;
      align-items: baseline;
      gap: 10px;
      padding-top: 14px;
    }

    .metric-value {
      font-size: clamp(2rem, 5vw, 3.3rem);
      line-height: 1;
      font-weight: 850;
      color: var(--ink);
    }

    .metric-suffix { color: var(--muted); font-weight: 750; }
    .table-wrap { padding: 14px 16px 18px; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }

    th {
      text-align: left;
      color: #475569;
      background: #f1f5f9;
      font-size: 0.76rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    th, td { padding: 10px 12px; border-bottom: 1px solid #e8eef5; }
    td { color: #1f2937; font-weight: 620; }

    .sql { margin-top: auto; border-top: 1px solid #edf2f7; background: #fbfdff; }
    details { padding: 10px 16px; }
    summary { cursor: pointer; color: var(--blue); font-weight: 750; font-size: 0.86rem; }

    pre {
      white-space: pre-wrap;
      word-break: break-word;
      margin: 10px 0 0;
      color: #334155;
      font-size: 0.78rem;
    }

    footer { color: var(--muted); padding: 0 0 32px; font-size: 0.9rem; }

    @media (max-width: 920px) {
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .result-card.wide { grid-column: span 2; }
    }

    @media (max-width: 640px) {
      .shell { width: min(100% - 22px, 1180px); }
      header { padding-top: 24px; }
      .grid { grid-template-columns: 1fr; gap: 12px; }
      .result-card.wide { grid-column: span 1; }
      .question { min-height: auto; }
      .metric-value { font-size: 2.35rem; }
    }
  </style>
</head>
<body>
  <header class="shell">
    <div class="eyebrow">PostgreSQL dashboard</div>
    <h1>GradCafe Query Results</h1>
    <p class="lede">A single Flask page displaying the 11 analysis queries from the <strong>{{ db_name }}</strong> database.</p>
    <div class="status-bar">
      <span class="pill">Database: {{ db_name }}</span>
      <span class="pill">Queries: {{ results|length }}</span>
      <span class="pill">Host: {{ db_host }}:{{ db_port }}</span>
    </div>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
  </header>

  <main class="shell grid">
    {% for result in results %}
      <section class="result-card {% if result.type == 'table' %}wide{% endif %}">
        <div class="card-head">
          <div class="number">Q{{ result.number }}</div>
          <h2>{{ result.title }}</h2>
        </div>
        <p class="question">{{ result.question }}</p>

        {% if result.error %}
          <div class="error">{{ result.error }}</div>
        {% elif result.type == 'metric' %}
          <div class="metric">
            <span class="metric-value">{{ result.value }}</span>
            <span class="metric-suffix">{{ result.suffix }}</span>
          </div>
        {% else %}
          <div class="table-wrap">
            <table>
              <thead>
                <tr>{% for column in result.columns %}<th>{{ column }}</th>{% endfor %}</tr>
              </thead>
              <tbody>
                {% for row in result.rows %}
                  <tr>{% for value in row %}<td>{{ value }}</td>{% endfor %}</tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        {% endif %}

        <div class="sql">
          <details>
            <summary>View SQL</summary>
            <pre>{{ result.sql.strip() }}</pre>
          </details>
        </div>
      </section>
    {% endfor %}
  </main>

  <footer class="shell">Refresh the page after updating data in PostgreSQL to rerun all queries.</footer>
</body>
</html>
"""


def create_db_connection():
    """This function creates DB connection"""
    try:
        return psycopg.connect(**DB_CONFIG)
    except OperationalError as error:
        raise RuntimeError(f"Could not connect to PostgreSQL: {error}") from error


def format_value(value):
    """This function formats value"""
    if value is None:
        return "N/A"
    if isinstance(value, Decimal):
        return f"{value:,.2f}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def run_query(connection, query_info):
    """This function run query and return result"""
    result = dict(query_info)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query_info["sql"])
            rows = cursor.fetchall()
            result["columns"] = [desc.name for desc in cursor.description]
    except Exception as error: # pylint: disable=broad-exception-caught
        result["error"] = str(error)
        result["columns"] = []
        result["rows"] = []
        result["value"] = "Error"
        return result

    formatted_rows = [[format_value(value) for value in row] for row in rows]
    result["rows"] = formatted_rows

    if query_info["type"] == "metric":
        result["value"] = formatted_rows[0][0] if formatted_rows and formatted_rows[0] else "N/A"

    return result


def get_results():
    """This query gets results from run_query"""
    with create_db_connection() as connection:
        return [run_query(connection, query_info) for query_info in QUERIES]


@app.route("/")
def index():
    """
    Render the GradCafe dashboard homepage with application results.

    Attempts to fetch results from the database and displays an error message
    on the page if the results cannot be loaded.
    """
    error = None
    results = []
    try:
        results = get_results()
    except RuntimeError as exc:
        error = str(exc)

    return render_template_string(
        TEMPLATE,
        results=results,
        error=error,
        db_name=DB_CONFIG["dbname"],
        db_host=DB_CONFIG["host"],
        db_port=DB_CONFIG["port"],
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
