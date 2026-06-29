"""Tests for Flask button routes."""

import os
import sys
import pytest
from pika.exceptions import AMQPError

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(PROJECT_DIR, "src")
WEB_DIR = os.path.join(SRC_DIR, "web")
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, WEB_DIR)

import web.app as flask_app  # pylint: disable=wrong-import-position


@pytest.mark.buttons
def test_pull_data_queues_task(monkeypatch):
    """Pull Data queues the scrape task."""
    called = {}

    def fake_publish_task(kind, payload=None):
        called["kind"] = kind
        called["payload"] = payload

    monkeypatch.setattr(flask_app, "publish_task", fake_publish_task)

    client = flask_app.app.test_client()
    response = client.post("/pull-data")

    assert response.status_code == 202
    assert response.get_json() == {
        "status": "queued",
        "task": "scrape_new_data",
    }
    assert called == {
        "kind": "scrape_new_data",
        "payload": {},
    }


@pytest.mark.buttons
def test_update_analysis_queues_task(monkeypatch):
    """Update Analysis queues the recompute task."""
    called = {}

    def fake_publish_task(kind, payload=None):
        called["kind"] = kind
        called["payload"] = payload

    monkeypatch.setattr(flask_app, "publish_task", fake_publish_task)

    client = flask_app.app.test_client()
    response = client.post("/update-analysis")

    assert response.status_code == 202
    assert response.get_json() == {
        "status": "queued",
        "task": "recompute_analytics",
    }
    assert called == {
        "kind": "recompute_analytics",
        "payload": {},
    }


@pytest.mark.buttons
def test_pull_data_publish_failure(monkeypatch):
    """Pull Data returns 503 when publishing fails."""
    def fake_publish_task(kind, payload=None):
        raise AMQPError("fake publish error")

    monkeypatch.setattr(flask_app, "publish_task", fake_publish_task)

    client = flask_app.app.test_client()
    response = client.post("/pull-data")

    assert response.status_code == 503
    assert response.get_json() == {"error": "publish_failed"}


@pytest.mark.buttons
def test_update_analysis_publish_failure(monkeypatch):
    """Update Analysis returns 503 when publishing fails."""
    def fake_publish_task(kind, payload=None):
        raise AMQPError("fake publish error")

    monkeypatch.setattr(flask_app, "publish_task", fake_publish_task)

    client = flask_app.app.test_client()
    response = client.post("/update-analysis")

    assert response.status_code == 503
    assert response.get_json() == {"error": "publish_failed"}
