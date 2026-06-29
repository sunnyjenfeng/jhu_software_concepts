"""Tests for worker consumer helpers."""

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "worker"))

consumer = importlib.import_module("consumer")


class ContextCursor:
    """Small cursor test double with context-manager support."""

    def __init__(self, rows=None):
        """Store fake query rows and executed statements."""
        self.rows = rows or []
        self.executed = []
        self.description = []
        self.rowcount = 1

    def execute(self, sql, params=None):
        """Record SQL and params passed by the code under test."""
        self.executed.append((sql, params))

    def fetchone(self):
        """Return the first fake row."""
        return self.rows[0] if self.rows else None

    def fetchall(self):
        """Return all fake rows."""
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ContextConnection:
    """Connection test double that returns a fixed cursor."""

    def __init__(self, cursor):
        """Store the cursor used by tests."""
        self.cursor_obj = cursor

    def cursor(self):
        """Return the fake cursor."""
        return self.cursor_obj

    def close(self):
        """Match the database connection interface."""


@pytest.mark.worker
def test_result_id():
    """Extract result ids from valid GradCafe URLs."""
    assert consumer.result_id("https://www.thegradcafe.com/result/12345") == 12345
    assert consumer.result_id(None) is None
    assert consumer.result_id("bad-url") is None

@pytest.mark.worker
def test_watermark_id():
    """Convert watermark values into integer ids."""
    assert consumer.watermark_id(None) == 0
    assert consumer.watermark_id("12345") == 12345
    assert consumer.watermark_id("https://www.thegradcafe.com/result/12345") == 12345

@pytest.mark.worker
def test_insert_scraped_applicants_counts_inserted_rows():
    """Count only rows inserted by ON CONFLICT-safe applicant inserts."""
    rowcounts = [1, 0]

    class FakeCursor:
        """Cursor that returns controlled row counts."""

        def __init__(self):
            """Initialize rowcount before execute is called."""
            self.rowcount = 0

        def execute(self, _sql, _params):
            """Set rowcount from the next fake result."""
            self.rowcount = rowcounts.pop(0)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def make_cursor():
        """Create a cursor for each insert call."""
        return FakeCursor()

    fake_conn = SimpleNamespace(cursor=make_cursor)

    rows = [
        {
            "Program Name": "CS",
            "University": "JHU",
            "Comments": "ok",
            "Date of Information Added to Grad Cafe": "2026-06-14",
            "URL link to applicant entry": "https://cafe.com/a",
            "Applicant Status": "Accepted",
            "Semester and Year of Program Start": "Fall 2026",
            "International / American Student": "American",
            "GPA": "3.9",
            "GRE Score": "320",
            "GRE V Score": "160",
            "GRE AW": "4.5",
            "Masters or PhD": "Masters",
        },
        {
            "Program Name": "CS",
            "University": "JHU",
            "URL link to applicant entry": "https://cafe.com/a",
        },
    ]

    assert consumer.insert_scraped_applicants(fake_conn, rows) == 1


@pytest.mark.worker
def test_open_rabbit_channel(monkeypatch):
    """Declare RabbitMQ exchange, queue, binding, and QoS."""
    class FakeChannel:
        """RabbitMQ channel test double."""

        def __init__(self):
            """Initialize declaration state."""
            self.exchange = None
            self.queue = None
            self.bind = None
            self.qos = None

        def exchange_declare(self, **kwargs):
            """Record exchange declaration arguments."""
            self.exchange = kwargs

        def queue_declare(self, **kwargs):
            """Record queue declaration arguments."""
            self.queue = kwargs

        def queue_bind(self, **kwargs):
            """Record queue binding arguments."""
            self.bind = kwargs

        def basic_qos(self, **kwargs):
            """Record QoS arguments."""
            self.qos = kwargs

    class FakeRabbitConnection:
        """RabbitMQ connection test double."""

        def __init__(self):
            """Create a fake channel."""
            self.channel_obj = FakeChannel()

        def channel(self):
            """Return the fake channel."""
            return self.channel_obj

        def close(self):
            """Match the RabbitMQ connection interface."""

    fake_connection = FakeRabbitConnection()
    monkeypatch.setenv("RABBITMQ_URL", "amqp://example")
    monkeypatch.setattr(consumer.pika, "URLParameters", lambda url: ("params", url))
    monkeypatch.setattr(consumer.pika, "BlockingConnection", lambda params: fake_connection)

    rabbit_conn, _channel = consumer.open_rabbit_channel()

    assert rabbit_conn is fake_connection
    assert fake_connection.channel_obj.qos == {"prefetch_count": 1}


@pytest.mark.worker
def test_get_and_update_last_seen():
    """Read and update the ingestion watermark."""
    cursor = ContextCursor(rows=[("123",)])
    conn = ContextConnection(cursor)

    assert consumer.get_last_seen(conn) == "123"
    consumer.update_last_seen(conn, "456")

    assert cursor.executed[0][1] == (consumer.SOURCE,)
    assert cursor.executed[1][1] == (consumer.SOURCE, "456")


@pytest.mark.worker
def test_get_last_seen_empty():
    """Return None when no watermark row exists."""
    assert consumer.get_last_seen(ContextConnection(ContextCursor())) is None


@pytest.mark.worker
def test_context_cursor_fetchall():
    """Return all rows from the context cursor fake."""
    assert ContextCursor(rows=[("row",)]).fetchall() == [("row",)]


@pytest.mark.worker
def test_load_new_records(monkeypatch, tmp_path):
    """Load only JSONL records newer than the saved watermark."""
    data_file = tmp_path / "records.jsonl"
    data_file.write_text(
        "\n".join(
            [
                "",
                json.dumps({"url": "https://www.thegradcafe.com/result/10"}),
                json.dumps({"url": "https://www.thegradcafe.com/result/12"}),
                json.dumps({"url": "bad"}),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(consumer, "DATA_FILE", str(data_file))

    assert consumer.load_new_records("https://www.thegradcafe.com/result/10") == [
        {"url": "https://www.thegradcafe.com/result/12"}
    ]


@pytest.mark.worker
def test_insert_applicants():
    """Insert cleaned applicant rows into the database."""
    cursor = ContextCursor()
    conn = ContextConnection(cursor)
    records = [
        {
            "program": "Program",
            "comments": "Comment",
            "date_added": "2026-01-01",
            "url": "https://cafe.com/1",
            "status": "Accepted",
            "term": "Fall 2026",
            "US/International": "American",
            "GPA": "",
            "GRE": "",
            "GRE V": "",
            "GRE AW": "",
            "Degree": "PhD",
            "llm-generated-program": "Program",
            "llm-generated-university": "University",
        }
    ]

    consumer.insert_applicants(conn, records)

    params = cursor.executed[0][1]
    assert params["gpa"] is None
    assert params["url"] == "https://cafe.com/1"


@pytest.mark.worker
def test_handle_scrape_new_data(monkeypatch):
    """Scrape, clean, insert, and update the newest seen id."""
    calls = {}

    monkeypatch.setattr(consumer, "scrape_data", lambda start_page, end_page: ["raw"])
    monkeypatch.setattr(
        consumer,
        "clean_data",
        lambda raw: [
            {
                "Program Name": "CS",
                "University": "JHU",
                "URL link to applicant entry": "https://www.thegradcafe.com/result/20",
            }
        ],
    )
    monkeypatch.setattr(
        consumer,
        "insert_scraped_applicants",
        lambda conn, records: calls.setdefault("records", records) or 1,
    )
    monkeypatch.setattr(
        consumer,
        "update_last_seen",
        lambda conn, last_seen: calls.setdefault("last_seen", last_seen),
    )

    consumer.handle_scrape_new_data(object(), {"start_page": 2, "end_page": 4})

    assert calls["records"][0]["Program Name"] == "CS"
    assert calls["last_seen"] == "20"


@pytest.mark.worker
def test_handle_scrape_new_data_no_ids(monkeypatch):
    """Skip watermark updates when no scraped records have ids."""
    calls = {}
    monkeypatch.setattr(consumer, "scrape_data", lambda start_page, end_page: [])
    monkeypatch.setattr(consumer, "clean_data", lambda raw: [])
    monkeypatch.setattr(consumer, "insert_scraped_applicants", lambda conn, records: 0)
    monkeypatch.setattr(
        consumer,
        "update_last_seen",
        lambda conn, last_seen: calls.setdefault("last_seen", last_seen),
    )

    consumer.handle_scrape_new_data(object(), {})

    assert not calls


@pytest.mark.worker
def test_handle_recompute_analytics(monkeypatch):
    """Run configured analytics queries and save their results."""
    class AnalyticsCursor(ContextCursor):
        """Cursor that returns one analytics row."""

        def execute(self, sql, params=None):
            """Record analytics SQL and expose a fake column name."""
            self.executed.append((sql, params))
            self.description = [SimpleNamespace(name="answer")]

        def fetchall(self):
            """Return one analytics result row."""
            return [(42, None)]

    cursor = AnalyticsCursor()
    conn = ContextConnection(cursor)
    monkeypatch.setattr(
        consumer,
        "QUERIES",
        [
            {"number": 1, "question": "Q1", "sql": "SELECT 1"},
            {"number": 2, "question": "Q2", "sql": "SELECT 2", "params": [1]},
        ],
    )

    consumer.handle_recompute_analytics(conn, {})

    assert len(cursor.executed) == 4
    assert cursor.executed[1][1][0] == 1
    assert cursor.executed[3][1][0] == 2


@pytest.mark.worker
def test_process_message_success_and_failure(monkeypatch):
    """Commit successful messages and roll back failed messages."""
    class FakeDb:
        """Database connection test double."""

        def __init__(self):
            """Initialize transaction state."""
            self.committed = False
            self.rolled_back = False
            self.closed = False

        def commit(self):
            """Record a commit."""
            self.committed = True

        def rollback(self):
            """Record a rollback."""
            self.rolled_back = True

        def close(self):
            """Record connection close."""
            self.closed = True

    class FakeChannel:
        """RabbitMQ channel test double for acknowledgements."""

        def __init__(self):
            """Initialize ack and nack state."""
            self.ack = None
            self.nack = None

        def basic_ack(self, delivery_tag):
            """Record acknowledged delivery tag."""
            self.ack = delivery_tag

        def basic_nack(self, delivery_tag, requeue):
            """Record rejected delivery tag and requeue flag."""
            self.nack = (delivery_tag, requeue)

    method = SimpleNamespace(delivery_tag="tag")
    db_conn = FakeDb()
    channel = FakeChannel()
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setattr(consumer.psycopg, "connect", lambda url: db_conn)
    monkeypatch.setattr(consumer, "TASKS", {"ok": lambda conn, payload: None})

    consumer.process_message(channel, method, None, b'{"kind":"ok","payload":{"a":1}}')

    assert db_conn.committed is True
    assert db_conn.closed is True
    assert channel.ack == "tag"

    failing_db = FakeDb()
    failing_channel = FakeChannel()
    monkeypatch.setattr(consumer.psycopg, "connect", lambda url: failing_db)
    monkeypatch.setattr(
        consumer,
        "TASKS",
        {"bad": lambda conn, payload: (_ for _ in ()).throw(ValueError("boom"))},
    )

    with pytest.raises(ValueError):
        consumer.process_message(failing_channel, method, None, b'{"kind":"bad"}')

    assert failing_db.rolled_back is True
    assert failing_db.closed is True
    assert failing_channel.nack == ("tag", False)


@pytest.mark.worker
def test_main(monkeypatch):
    """Register the consumer callback and start consuming."""
    class FakeChannel:
        """RabbitMQ channel test double for main."""

        def __init__(self):
            """Initialize consumer state."""
            self.consume = None
            self.started = False

        def basic_consume(self, **kwargs):
            """Record basic_consume arguments."""
            self.consume = kwargs

        def start_consuming(self):
            """Record that consuming started."""
            self.started = True

    channel = FakeChannel()
    monkeypatch.setattr(consumer, "open_rabbit_channel", lambda: ("rabbit", channel))

    consumer.main()

    assert channel.consume["queue"] == consumer.QUEUE
    assert channel.started is True
