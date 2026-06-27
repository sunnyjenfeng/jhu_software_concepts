# This script test two .py files: load_data.py and query_data.py

import importlib
import io
import json
import os
import sys

import pytest
from psycopg import OperationalError


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(PROJECT_DIR, "src")
sys.path.insert(0, SRC_DIR)

def make_error_cursor():
    def execute(query):
        raise OperationalError("fake error")

    def fetchall():
        return []

    return type(
        "ErrorCursor",
        (),
        {
            "execute": staticmethod(execute),
            "fetchall": staticmethod(fetchall),
        },
    )()


def make_error_connection():
    def cursor():
        return make_error_cursor()

    return type(
        "ErrorConnection",
        (),
        {
            "cursor": staticmethod(cursor),
            "autocommit": False,
        },
    )()

def make_fake_cursor():
    def execute(query, params=None):
        pass

    # def fetchall():
    #     return [(1,)]
    def fetchall():
        return [(3.9, 320.0, 160.0, 4.5)]

    def close():
        pass

    return type(
        "FakeCursor",
        (),
        {
            "execute": staticmethod(execute),
            "fetchall": staticmethod(fetchall),
            "close": staticmethod(close),
        },
    )()


def make_fake_connection():
    def cursor():
        return make_fake_cursor()

    def close():
        pass

    fake_connection = type(
        "FakeConnection",
        (),
        {
            "cursor": staticmethod(cursor),
            "close": staticmethod(close),
            "autocommit": False,
        },
    )()

    return fake_connection


def fake_open(*args, **kwargs):
    fake_row = {
        "program": "Program A",
        "comments": "Test comment",
        "date_added": "2026-06-14",
        "url": "https://cafe.com/a",
        "status": "Accepted",
        "term": "Fall 2026",
        "US/International": "American",
        "GPA": "3.90",
        "GRE": "320",
        "GRE V": "160",
        "GRE AW": "4.5",
        "Degree": "PhD",
        "llm-generated-program": "Program A",
        "llm-generated-university": "University A",
    }

    return io.StringIO(json.dumps(fake_row))


@pytest.mark.db
def test_load_data_module(monkeypatch):
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("psycopg.connect", lambda **kwargs: make_fake_connection())

    load_data = importlib.import_module("load_data")

    assert load_data.format_text("Bob's Program") == "'Bob''s Program'"
    assert load_data.format_text(None) == "NULL"
    assert load_data.format_float("") == "NULL"
    assert load_data.format_float("3.90") == "3.9"


@pytest.mark.db
def test_query_data_module(monkeypatch):
    monkeypatch.setattr("psycopg.connect", lambda **kwargs: make_fake_connection())

    query_data = importlib.import_module("query_data")

    assert query_data.create_db_connection("db", "user", "pw", "host", "5432") is not None
    # assert query_data.execute_read_query(make_fake_connection(), "SELECT count(*)") == [(1,)]
    assert query_data.execute_read_query(make_fake_connection(), "SELECT count(*)") == [(3.9, 320.0, 160.0, 4.5)]

@pytest.mark.db
def test_load_data_error_paths(monkeypatch):
    load_data = importlib.import_module("load_data")

    def fake_connect(*args, **kwargs):
        raise OperationalError("fake error")

    monkeypatch.setattr("psycopg.connect", fake_connect)

    assert load_data.create_system_connection("postgres", "181818") is None
    assert load_data.create_db_connection("db", "user", "pw", "host", "5432") is None

    load_data.create_database(make_error_connection(), "bad_db")
    load_data.execute_query(make_error_connection(), "BAD SQL")

    assert load_data.execute_read_query(make_error_connection(), "BAD SQL") is None


@pytest.mark.db
def test_query_data_success_and_error_paths(monkeypatch):
    query_data = importlib.import_module("query_data")

    def fake_connect(*args, **kwargs):
        raise OperationalError("fake error")

    query_data.execute_query(make_fake_connection(), "SELECT 1")

    assert query_data.execute_read_query(make_error_connection(), "BAD SQL") is None

    monkeypatch.setattr("psycopg.connect", fake_connect)

    assert query_data.create_db_connection("db", "user", "pw", "host", "5432") is None
    query_data.execute_query(make_error_connection(), "BAD SQL")