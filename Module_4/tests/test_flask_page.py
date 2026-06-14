# %%
import os
import sys
import pytest

# CURRENT_DIR = os.getcwd() # this depends on where I run pytest from.

#  __file__ uses the actual location of test_flask_page.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)  # this moves up one level(to the parent folder)
SRC_DIR = os.path.join(PROJECT_DIR, "src") #this goes to Module_4/src


# %%

sys.path.insert(0, SRC_DIR) #add src folder to the front of Python’s import search list

import app as flask_app #import app.py as a module

# %%
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
def test_get_analysis_status200():
    """
    Test GET 
    Test status code 200
    """
    flask_app.app.config.update(TESTING=True) #turns on testing mode for flask

    client = flask_app.app.test_client() #It creates a test client, which acts like a fake browser.

    response = client.get("/")

    assert response.status_code == 200

# %%

@pytest.mark.web
def test_page_has_buttons():
    """
    Test page has both “Pull Data” and “Update Analysis” buttons
    """
    flask_app.app.config.update(TESTING=True)
    client = flask_app.app.test_client()

    response = client.get("/")
    
    #Gets the HTML response as normal text, so I can search
    page_text = response.get_data(as_text=True) 

    assert '<button type="submit">Pull Data</button>' in page_text
    assert '<button type="submit">Update Analysis</button>' in page_text

# %%
@pytest.mark.web
def test_analysis_page_has_analysis_and_answer():

    """​
    Test Page text includes “Analysis” and at least one “Answer”
    """
    flask_app.app.config.update(TESTING=True)
    client = flask_app.app.test_client()

    response = client.get("/")

    #Gets the HTML response as normal text, so I can search
    page_text = response.get_data(as_text=True) 

    assert "Analysis" in page_text
    assert "Answer:" in page_text

# %%


# %%


# %%



