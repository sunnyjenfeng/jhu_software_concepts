# %%
import os
import sys
import pytest

#  __file__ uses the actual location of test_flask_page.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)  # this moves up one level(to the parent folder)
SRC_DIR = os.path.join(PROJECT_DIR, "src") #this goes to Module_4/src


sys.path.insert(0, SRC_DIR) #add src folder to the front of Python’s import search list

import app as flask_app #import app.py as a module


# %%
import io
import json
from types import SimpleNamespace

# %%

@pytest.mark.buttons
def test_pull_data_button(monkeypatch):
    """   ​
    Test pull-data 
​    1. Returns 200
    ​2. Triggers the loader with the rows from the scraper (should be faked / mocked)
    """
    # fake_rows is fake scraper data.
    # loaded is an empty dictionary used to remember what rows got passed into the loader function.
    fake_rows = [{"Program Name": "Test Program"}]
    loaded = {}

    # Turns on Flask testing mode.
    flask_app.app.config.update(TESTING=True)

    # Pull_data_running=True/False is a binary var in my original code. 
    # Force pull_data_running to be False, so the route behaves like it is allowed to run
    monkeypatch.setattr(flask_app, "pull_data_running", False)
    
    #Replaces real database connection function.
    #Instead of connecting to PostgreSQL, it returns a fake object with a .close() method.
    # it acts like : 
    # conn = create_db_connection(...)
    # ...
    # conn.close()
    monkeypatch.setattr(flask_app,
                        "create_db_connection",
                        lambda *args: SimpleNamespace(close=lambda: None),)
    
    # Replaces this real behavior:
    # run_module_2_script("scrape.py")
    # run_module_2_script("clean.py")
    # So the test does not actually run  scraper or cleaner.
    monkeypatch.setattr(flask_app, "run_module_2_script", lambda script_name: None)


    # The app normally opens a JSON file: applicant_data.json. 
    # This replaces open() with a fake file containing:[{"Program Name": "Test Program"}]
    monkeypatch.setattr("builtins.open",
                     lambda *args, **kwargs: io.StringIO(json.dumps(fake_rows)),)

    monkeypatch.setattr(flask_app,
                        "insert_new_applicants",
                        lambda connection, rows: loaded.setdefault("rows", rows) or 1,)

    monkeypatch.setattr(flask_app,
                        "run_query",
                        lambda connection, query: {
                            "number": query["number"],
                            "question": query["question"],
                            "columns": [],
                            "rows": [],
                            "error": None,
                        },)
    # Creates a fake browser for testing Flask routes.
    client = flask_app.app.test_client()

    # Flask follows the redirect back to the homepage.
    response = client.post("/pull-data", follow_redirects=True)

    assert response.status_code == 200
    # Checks that the fake scraper rows were passed into the loader function.
    assert loaded["rows"] == fake_rows

# %%

@pytest.mark.buttons
def test_update_analysis_button(monkeypatch):
    """
    Test POST /update-analysis 
    ​Returns 200 when not busy
    """
    flask_app.app.config.update(TESTING=True)
    monkeypatch.setattr(flask_app, "pull_data_running", False)

    client = flask_app.app.test_client()
    response = client.post("/update-analysis", follow_redirects=True)

    assert response.status_code == 200

# %%
@pytest.mark.buttons
def test_update_analysis_busy_gating(monkeypatch):
    """
    Test busy gating
    1. ​When a pull is “in progress”, POST /update-analysis returns 409 (and performs no update).
​    2. When busy(pull is “in progress”), POST /pull-data returns 409
    """
    flask_app.app.config.update(TESTING=True)

    # pretends that Pull Data is already running.
    monkeypatch.setattr(flask_app, "pull_data_running", True)

    client = flask_app.app.test_client()

    # Another POST request to /update_analysis should return 409.
    assert client.post("/update-analysis").status_code == 409

    # Another POST request to /pull-data should return 409.
    assert client.post("/pull-data").status_code == 409

# %%



