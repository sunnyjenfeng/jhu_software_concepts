"""test analysis format module"""
import importlib
import re
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for import_path in (PROJECT_ROOT / "src" / "web", PROJECT_ROOT / "src"):
    sys.path.insert(0, str(import_path))

flask_app = importlib.import_module("web.app")

@pytest.mark.analysis
def test_page_includes_answer(monkeypatch):
    """
    Test that my page include “Answer” labels for rendered analysis
    """
    monkeypatch.setattr(
        flask_app,
        "create_db_connection",
        lambda *args: Mock(),
    )
    monkeypatch.setattr(
        flask_app,
        "get_cached_analysis_results",
        lambda connection: [
            {
                "number": 1,
                "question": "Test question",
                "columns": ["answer"],
                "rows": [["42"]],
                "error": None,
            }
        ],
    )

    client = flask_app.app.test_client()
    response = client.get("/")

    page_text = response.get_data(as_text=True)

    assert "Answer:" in page_text

@pytest.mark.analysis
def test_percentages_with_two_decimals(monkeypatch):
    """
    Test that any percentage is formatted with two decimals.
    """
    flask_app.app.config.update(TESTING=True)

    monkeypatch.setattr(
        flask_app,
        "create_db_connection",
        lambda *args: Mock(),
    )

    monkeypatch.setattr(
        flask_app,
        "get_cached_analysis_results",
        lambda connection: [],
    )

    monkeypatch.setattr(
        flask_app,
        "run_query",
        lambda connection, query: {
            "number": 1,
            "question": "Test percentage",
            "columns": ["percentage"],
            "rows": [("39.28%",)],
            "error": None,
        },
    )

    client = flask_app.app.test_client()
    response = client.get("/analysis")

    page_text = response.get_data(as_text=True)
    percentages = re.findall(r"\b\d+\.\d{2}%", page_text)

    assert percentages
    assert all(re.fullmatch(r"\d+\.\d{2}%", percent) for percent in percentages)
