import importlib
import io
import json
import os
import sys
from types import SimpleNamespace

import pytest
from psycopg import OperationalError


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(PROJECT_DIR, "src")
sys.path.insert(0, SRC_DIR)


class FakeCursor:
    def __init__(self, error=False):
        self.error = error
        self.query = ""

    def execute(self, query):
        self.query = query
        if self.error:
            raise OperationalError("fake error")

    def fetchall(self):
        query = self.query.lower()
        if "round(avg(gpa)::numeric" in query and "avg_gre" in query:
            return [(3.9, 320.0, 160.0, 4.5)]
        if "select * from applicants limit 10" in query:
            return [(1, "Program A")]
        if "select count(*)" in query:
            return [(1,)]
        if "distinct term" in query:
            return [("Fall 2026",)]
        if "distinct status" in query:
            return [("Accepted",)]
        if "distinct degree" in query:
            return [("PhD",)]
        if "distinct us_or_international" in query:
            return [("American", 1)]
        return [(64.23,)]

    def close(self):
        pass


class FakeConnection:
    def __init__(self, error=False):
        self.error = error
        self.autocommit = False

    def cursor(self):
        return FakeCursor(error=self.error)

    def close(self):
        pass


def fake_open(*args, **kwargs):
    rows = [
        {
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
        },
        {
            "program": None,
            "comments": None,
            "date_added": None,
            "url": None,
            "status": None,
            "term": None,
            "US/International": None,
            "GPA": None,
            "GRE": None,
            "GRE V": None,
            "GRE AW": None,
            "Degree": None,
            "llm-generated-program": None,
            "llm-generated-university": None,
        },
    ]
    return io.StringIO("\n".join(json.dumps(row) for row in rows))


@pytest.mark.db
def test_load_data_module(monkeypatch):
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("psycopg.connect", lambda **kwargs: FakeConnection())
    sys.modules.pop("load_data", None)

    load_data = importlib.import_module("load_data")

    assert load_data.format_text("Bob's Program") == "'Bob''s Program'"
    assert load_data.format_text(None) == "NULL"
    assert load_data.format_float("") == "NULL"
    assert load_data.format_float("3.90") == "3.9"
    assert load_data.execute_read_query(FakeConnection(), "SELECT count(*)") == [(1,)]
    assert load_data.create_system_connection("postgres", "181818") is not None
    assert load_data.create_db_connection("db", "user", "pw", "host", "5432") is not None


@pytest.mark.db
def test_load_data_error_paths(monkeypatch):
    monkeypatch.setattr("psycopg.connect", lambda **kwargs: (_ for _ in ()).throw(OperationalError("fake error")))

    import load_data

    assert load_data.create_system_connection("postgres", "181818") is None
    assert load_data.create_db_connection("db", "user", "pw", "host", "5432") is None
    load_data.create_database(FakeConnection(error=True), "bad_db")
    load_data.execute_query(FakeConnection(error=True), "BAD SQL")
    assert load_data.execute_read_query(FakeConnection(error=True), "BAD SQL") is None


@pytest.mark.db
def test_query_data_module(monkeypatch):
    monkeypatch.setattr("psycopg.connect", lambda **kwargs: FakeConnection())
    sys.modules.pop("query_data", None)

    query_data = importlib.import_module("query_data")

    assert query_data.create_db_connection("db", "user", "pw", "host", "5432") is not None
    assert query_data.execute_read_query(FakeConnection(), "SELECT count(*)") == [(1,)]
    query_data.execute_query(FakeConnection(), "CREATE TABLE test(id int)")


@pytest.mark.db
def test_query_data_error_paths(monkeypatch):
    monkeypatch.setattr("psycopg.connect", lambda **kwargs: (_ for _ in ()).throw(OperationalError("fake error")))

    import query_data

    assert query_data.create_db_connection("db", "user", "pw", "host", "5432") is None
    query_data.execute_query(FakeConnection(error=True), "BAD SQL")
    assert query_data.execute_read_query(FakeConnection(error=True), "BAD SQL") is None
