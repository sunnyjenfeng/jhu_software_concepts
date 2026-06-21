# %%
import os
import sys
import pytest

import io
import json
from types import SimpleNamespace
from psycopg import OperationalError



#  __file__ uses the actual location of test_flask_page.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)  # this moves up one level(to the parent folder)
SRC_DIR = os.path.join(PROJECT_DIR, "src") #this goes to Module_4/src


sys.path.insert(0, SRC_DIR) #add src folder to the front of Python’s import search list

import app as flask_app #import app.py as a module


@pytest.mark.db
def test_pull_data_inserts_rows(monkeypatch):
    """
    Test insert on pull. 
​    1. Before: target table empty
    ​2. After POST/pull-data new rows exist with required (non-null) fields
    """
    # this create one fake row
    fake_rows = [
        {
            "Program Name": "Test Program",
            "University": "Test University",
            "Comments": "Test comment",
            "Date of Information Added to Grad Cafe": "2026-06-14",
            "URL link to applicant entry": "https://cafe.com/testdata",
            "Applicant Status": "Accepted",
            "Semester and Year of Program Start": "Fall 2026",
            "International / American Student": "American",
            "GPA": "3.90",
            "GRE Score": "320",
            "GRE V Score": "160",
            "GRE AW": "4.5",
            "Masters or PhD": "PhD",
        }
    ]

    # conn = flask_app.create_db_connection(
    #     "gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432"
    # )
    conn = flask_app.create_db_connection()
    
    cur = conn.cursor()

    # Before: data is empty
    # cur.execute("DELETE FROM applicants;")
    conn.commit()

    # confirms the table is empty before testing /pull-data.
    cur.execute("SELECT COUNT(*) FROM applicants;")
    assert cur.fetchone()[0] == 0

    monkeypatch.setattr(flask_app, "pull_data_running", False)

    # Prevents the test from running scrape.py and clean.py:
    monkeypatch.setattr(flask_app, "run_module_2_script", lambda script_name: None)
    
    # Fakes opening applicant_data.json.
    # Instead of reading the real file,  the app uses fake_rows.      
    monkeypatch.setattr(
        "builtins.open",
        lambda *args, **kwargs: io.StringIO(json.dumps(fake_rows)),
    )

    client = flask_app.app.test_client()
    client.post("/pull-data")

    cur.execute(
        """
        SELECT COUNT(*)
        FROM applicants
        WHERE program IS NOT NULL
          AND url IS NOT NULL
          AND status IS NOT NULL;
        """
    )
    # confirms new rows exist after /pull-data
    assert cur.fetchone()[0] > 0

    cur.close()
    conn.close()

# %%

@pytest.mark.db
def test_pull_data_does_not_insert_duplicates(monkeypatch):
    """
    Check Duplicate rows do not create duplicates in database
    (accidentally pulling the same data should not result in the database acquiring duplicated rows)
    """
    fake_rows = [
        {
            "Program Name": "Test Program",
            "University": "Test University",
            "Comments": "Test comment",
            "Date of Information Added to Grad Cafe": "2026-06-14",
            "URL link to applicant entry": "https://cafe.com/testdata",
            "Applicant Status": "Accepted",
            "Semester and Year of Program Start": "Fall 2026",
            "International / American Student": "American",
            "GPA": "3.90",
            "GRE Score": "320",
            "GRE V Score": "160",
            "GRE AW": "4.5",
            "Masters or PhD": "PhD",
        }
    ]

    # conn = flask_app.create_db_connection(
    #     "gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432"
    # )

    conn = flask_app.create_db_connection()

    cur = conn.cursor()
    # cur.execute("DELETE FROM applicants;")
    conn.commit()

    monkeypatch.setattr(flask_app, "pull_data_running", False)
    monkeypatch.setattr(flask_app, "run_module_2_script", lambda script_name: None)
    monkeypatch.setattr(
        "builtins.open",
        lambda *args, **kwargs: io.StringIO(json.dumps(fake_rows)),
    )

    client = flask_app.app.test_client()

    # callpull_data twice
    client.post("/pull-data")
    client.post("/pull-data")

    cur.execute(
        """
        SELECT COUNT(*)
        FROM applicants
        WHERE url = 'https://cafe.com/testdata';
        """
    )

    assert cur.fetchone()[0] == 1

    cur.close()
    conn.close()

# %%

@pytest.mark.db
def test_run_query_returns_expected_keys():
    """
    Test simple query function
    Query the data to return a dict with our expected keys (the required data fields within M3).
    SimpleNamespace is used to make a simple fake object.
    """
    fake_cursor = SimpleNamespace(
        description=[
            SimpleNamespace(name="p_id"),
            SimpleNamespace(name="program"),
            SimpleNamespace(name="comments"),
            SimpleNamespace(name="date_added"),
            SimpleNamespace(name="url"),
            SimpleNamespace(name="status"),
            SimpleNamespace(name="term"),
            SimpleNamespace(name="us_or_international"),
            SimpleNamespace(name="gpa"),
            SimpleNamespace(name="gre"),
            SimpleNamespace(name="gre_v"),
            SimpleNamespace(name="gre_aw"),
            SimpleNamespace(name="degree"),
            SimpleNamespace(name="llm_generated_program"),
            SimpleNamespace(name="llm_generated_university"),
        ],
        execute=lambda sql: None,
        fetchall=lambda: [
            (
                1,
                "Test Program",
                "Test comment",
                "2026-06-14",
                "https://cafe.com/testdata",
                "Accepted",
                "Fall 2026",
                "American",
                3.9,
                320,
                160,
                4.5,
                "PhD",
                "Test Program",
                "Test University",
            )
        ],
        close=lambda: None,
    )

    fake_connection = SimpleNamespace(cursor=lambda: fake_cursor)

    query = {
        "number": 1,
        "question": "Test question",
        "sql": "SELECT * FROM applicants;",
    }

    result = flask_app.run_query(fake_connection, query)

    assert set(result.keys()) == {"number", "question", "columns", "rows", "error"}
    assert result["number"] == 1
    assert result["question"] == "Test question"
    assert result["columns"] == [
        "p_id",
        "program",
        "comments",
        "date_added",
        "url",
        "status",
        "term",
        "us_or_international",
        "gpa",
        "gre",
        "gre_v",
        "gre_aw",
        "degree",
        "llm_generated_program",
        "llm_generated_university",
    ]
    assert result["rows"] == [
        (
            1,
            "Test Program",
            "Test comment",
            "2026-06-14",
            "https://cafe.com/testdata",
            "Accepted",
            "Fall 2026",
            "American",
            3.9,
            320,
            160,
            4.5,
            "PhD",
            "Test Program",
            "Test University",
        )
    ]
    assert result["error"] is None

#-------------- below are added for coverage --------------
# @pytest.mark.db
# def test_create_db_connection_error(monkeypatch):
#     def fake_connect(**kwargs):
#         raise OperationalError("fake error")

#     monkeypatch.setattr(flask_app.psycopg, "connect", fake_connect)

#     # assert flask_app.create_db_connection("db", "user", "pw", "host", "5432") is None
#     assert flask_app.create_db_connection()

@pytest.mark.db
def test_create_db_connection_error(monkeypatch):
    def fake_connect(*args, **kwargs):
        raise OperationalError("fake error")

    monkeypatch.setattr(flask_app.psycopg, "connect", fake_connect)

    assert flask_app.create_db_connection() is None

@pytest.mark.db
def test_insert_new_applicants_program_fallback():
    captured = {}
    fake_cursor = SimpleNamespace(rowcount=1)

    fake_cursor.execute = lambda sql, row: captured.update({"row": row})
    fake_cursor.close = lambda: None

    fake_connection = SimpleNamespace(
        cursor=lambda: fake_cursor,
        commit=lambda: None,
    )

    rows = [{"Program Name": "Only Program"}]

    assert flask_app.insert_new_applicants(fake_connection, rows) == 1
    assert captured["row"]["program"] == "Only Program"





