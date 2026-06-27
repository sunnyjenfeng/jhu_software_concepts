# %%
import os
import sys
import pytest

import io
import json
from types import SimpleNamespace

#  __file__ uses the actual location of test_flask_page.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)  # this moves up one level(to the parent folder)
SRC_DIR = os.path.join(PROJECT_DIR, "src") #this goes to Module_4/src


sys.path.insert(0, SRC_DIR) #add src folder to the front of Python’s import search list

import web.app as flask_app #import app.py as a module

# %%

@pytest.mark.integration
def test_integration_end_to_end(monkeypatch):
    """
    Integration test. ​End-to-end (pull -> update -> Render).
    ​1. Inject a fake scraper that returns multiple records
    ​2. POST /pull-data succeeds and rows are in DB
    ​3. POST /update-analysis succeeds (when not busy)
    ​4. GET /analysis shows updated analysis with correctly formatted
    """
    fake_rows = [
        {
            "Program Name": "Program A",
            "University": "University A",
            "Comments": "Test comment A",
            "Date of Information Added to Grad Cafe": "2026-06-14",
            "URL link to applicant entry": "https://cafe.com/test-a",
            "Applicant Status": "Accepted",
            "Semester and Year of Program Start": "Fall 2026",
            "International / American Student": "American",
            "GPA": "3.90",
            "GRE Score": "320",
            "GRE V Score": "160",
            "GRE AW": "4.5",
            "Masters or PhD": "PhD",
        },
        {
            "Program Name": "Program B",
            "University": "University B",
            "Comments": "Test comment B",
            "Date of Information Added to Grad Cafe": "2026-06-14",
            "URL link to applicant entry": "https://cafe.com/test-b",
            "Applicant Status": "Rejected",
            "Semester and Year of Program Start": "Spring 2027",
            "International / American Student": "International",
            "GPA": "3.60",
            "GRE Score": "310",
            "GRE V Score": "155",
            "GRE AW": "4.0",
            "Masters or PhD": "Masters",
        },
    ]

    # conn = flask_app.create_db_connection(
    #     "gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432"
    # )
    conn = flask_app.create_db_connection()

    cur = conn.cursor()
    cur.execute("DELETE FROM applicants;")
    conn.commit()

    monkeypatch.setattr(flask_app, "PULL_DATA_RUNNING", False)
    monkeypatch.setattr(flask_app, "run_module_2_script", lambda script_name: None)
    monkeypatch.setattr(
        "builtins.open",
        lambda *args, **kwargs: io.StringIO(json.dumps(fake_rows)),
    )

    client = flask_app.app.test_client()

    # Test pull-data button
    pull_response = client.post("/pull-data", follow_redirects=True)
    assert pull_response.status_code == 200
    
    # this test one query
    cur.execute("SELECT COUNT(*) FROM applicants;")
    row_count = cur.fetchone()[0]

    assert isinstance(row_count, int)
    assert row_count == 2

    # this test a second query
    cur.execute(
        """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE term = 'Fall 2026'
        AND status ILIKE '%Accepted%';
        """
    )

    average_gpa = cur.fetchone()[0]

    assert len(str(average_gpa).split(".")[1]) == 2

    # Test update-analysis button
    update_response = client.post("/update-analysis", follow_redirects=True)
    assert update_response.status_code == 200

    render_response = client.get("/")
    page_text = render_response.get_data(as_text=True)

    assert render_response.status_code == 200
    # confirms the rendered analysis output appears on the page.
    assert "Answer:" in page_text

    cur.close()
    conn.close()

# %%
# integration overlapping test:
# first pull:  A
# second pull: A + B
# expected DB: A + B

# %%

@pytest.mark.integration
def test_pull_data_twice_with_overlapping_data(monkeypatch):
    """
    Running POST /pull-data twice with overlapping data remains consistent with uniqueness policy
    integration overlapping test:
    first pull:  A
    second pull: A + B
    expected DB: A + B
    """
    row_a = {
        "Program Name": "Program A",
        "University": "University A",
        "Comments": "Test comment A",
        "Date of Information Added to Grad Cafe": "2026-06-14",
        "URL link to applicant entry": "https://cafe.com/test-a",
        "Applicant Status": "Accepted",
        "Semester and Year of Program Start": "Fall 2026",
        "International / American Student": "American",
        "GPA": "3.90",
        "GRE Score": "320",
        "GRE V Score": "160",
        "GRE AW": "4.5",
        "Masters or PhD": "PhD",
    }

    row_b = {
        "Program Name": "Program B",
        "University": "University B",
        "Comments": "Test comment B",
        "Date of Information Added to Grad Cafe": "2026-06-14",
        "URL link to applicant entry": "https://cafe.com/test-b",
        "Applicant Status": "Rejected",
        "Semester and Year of Program Start": "Fall 2026",
        "International / American Student": "International",
        "GPA": "3.60",
        "GRE Score": "310",
        "GRE V Score": "155",
        "GRE AW": "4.0",
        "Masters or PhD": "Masters",
    }

    first_pull = [row_a]
    second_pull = [row_a, row_b]

    # conn = flask_app.create_db_connection(
    #     "gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432"
    # )

    conn = flask_app.create_db_connection()

    cur = conn.cursor()
    cur.execute("DELETE FROM applicants;")
    conn.commit()

    fake_pulls = [first_pull, second_pull]

    monkeypatch.setattr(flask_app, "PULL_DATA_RUNNING", False)
    monkeypatch.setattr(flask_app, "run_module_2_script", lambda script_name: None)
    monkeypatch.setattr(
        "builtins.open",
        lambda *args, **kwargs: io.StringIO(json.dumps(fake_pulls.pop(0))),
    )

    client = flask_app.app.test_client()
    
    # call pull_data twice
    client.post("/pull-data")
    client.post("/pull-data")

    cur.execute("SELECT COUNT(*) FROM applicants;")
    assert cur.fetchone()[0] == 2

    cur.execute("SELECT COUNT(*) FROM applicants WHERE url = 'https://cafe.com/test-a';")
    assert cur.fetchone()[0] == 1

    cur.close()
    conn.close()

# %%



