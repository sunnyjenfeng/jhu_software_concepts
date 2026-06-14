# %%
import re

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

@pytest.mark.analysis 
def test_page_includes_answer():
    """
    Test that my page include “Answer” labels for rendered analysis
    """
    client = flask_app.app.test_client()
    response = client.get("/")

    page_text = response.get_data(as_text=True)

    assert "Answer:" in page_text


@pytest.mark.analysis 
def test_percentages_with_two_decimals():
    """
    Test that any percentage is formatted with two decimals.
    """
    client = flask_app.app.test_client()
    response = client.get("/")

    page_text = response.get_data(as_text=True)
    # find all decimal numbers on the page
    percentages = re.findall(r"\b\d+\.\d+\b", page_text)

    assert all(re.fullmatch(r"\d+\.\d{2}", percent) for percent in percentages)


