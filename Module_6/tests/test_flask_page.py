"""This test flask page"""
import importlib
import sys
import runpy
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for import_path in (PROJECT_ROOT / "src" / "web", PROJECT_ROOT / "src"):
    sys.path.insert(0, str(import_path))

flask_app = importlib.import_module("web.app")

def fake_db(monkeypatch):
    """fake db"""
    class FakeConnection:
        """Fake database connection."""

        def close(self):
            """Match the real connection interface."""

        def commit(self):
            """Provide a second public method for pylint."""

    result = {
        "number": 7,
        "question": "Flask page test question",
        "columns": ["page_answer"],
        "rows": [["page value"]],
        "error": None,
    }

    def create_connection(*_args):
        """Return a fake database connection."""
        return FakeConnection()

    def cached_results(_connection):
        """Return one fake analysis result."""
        return [result]

    monkeypatch.setattr(flask_app, "create_db_connection", create_connection)
    monkeypatch.setattr(flask_app, "get_cached_analysis_results", cached_results)


@pytest.mark.web
def test_create_app_with_test_config_again():
    """test create app"""
    test_app = flask_app.create_app({"TESTING": True})
    assert test_app.config["TESTING"] is True

@pytest.mark.web #This marks that this test as a web-related test.
def test_flask_app_testing_config():
    """
    Turn on testing mode for my Flask app, 
    Confirm that a flask app exists
    Then confirm that testing mode is turned on. 
    """
    flask_app.app.config.update(TESTING=True)

    assert flask_app.app is not None
    assert flask_app.app.config["TESTING"] is True

# %%
@pytest.mark.web
def test_required_routes_exist():
    """
    Gets all the route paths registered in my Flask app.
    Flask stored route definitions in flask_app.app.url_map
    """
    routes = {rule.rule for rule in flask_app.app.url_map.iter_rules()}

    assert "/" in routes
    assert "/pull-data" in routes
    assert "/update-analysis" in routes

# %%
@pytest.mark.web
def test_get_analysis_status200(monkeypatch):
    """
    Test GET 
    Test status code 200
    """
    flask_app.app.config.update(TESTING=True) #turns on testing mode for flask
    fake_db(monkeypatch)

    client = flask_app.app.test_client() #It creates a test client, which acts like a fake browser.

    response = client.get("/analysis")

    assert response.status_code == 200

# %%

@pytest.mark.web
def test_page_has_buttons(monkeypatch):
    """
    Test page has both “Pull Data” and “Update Analysis” buttons
    """
    flask_app.app.config.update(TESTING=True)
    fake_db(monkeypatch)
    client = flask_app.app.test_client()
    response = client.get("/analysis")
    #Gets the HTML response as normal text, so I can search
    page_text = response.get_data(as_text=True)
    assert 'data-testid="pull-data-btn"' in page_text
    assert 'data-testid="update-analysis-btn"' in page_text

@pytest.mark.web
def test_analysis_page_has_analysis_and_answer(monkeypatch):
    """Test page text includes Analysis and at least one Answer."""
    flask_app.app.config.update(TESTING=True)
    fake_db(monkeypatch)
    client = flask_app.app.test_client()
    response = client.get("/analysis")
    #Gets the HTML response as normal text, so I can search
    page_text = response.get_data(as_text=True)
    assert "Analysis" in page_text
    assert "Answer:" in page_text

#--------------- below are added for coverage -------------------
@pytest.mark.web
def test_app_main_runs(monkeypatch):
    """this is main run to test app"""
    monkeypatch.setattr("flask.Flask.run", lambda self, host, port, debug: None)
    app_path = PROJECT_ROOT / "src" / "web" / "app.py"
    runpy.run_path(app_path, run_name="__main__")

@pytest.mark.web
def test_create_app_with_test_config():
    """config"""
    test_app = flask_app.create_app({"TESTING": True})
    assert test_app.config["TESTING"] is True
