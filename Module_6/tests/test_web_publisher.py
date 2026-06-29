"""test web publisher"""
import json
import os
import sys
import publisher

import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
WEB_DIR = os.path.join(PROJECT_DIR, "src", "web")
sys.path.insert(0, WEB_DIR)

class FakeChannel:
    """class for fake channel"""
    def __init__(self):
        """ini"""
        self.exchange = None
        self.queue = None
        self.bind = None
        self.confirmed = False
        self.published = None

    def exchange_declare(self, **kwargs):
        """exchange_declare"""
        self.exchange = kwargs

    def queue_declare(self, **kwargs):
        """queue declare"""
        self.queue = kwargs

    def queue_bind(self, **kwargs):
        """queue bind"""
        self.bind = kwargs

    def confirm_delivery(self):
        """confirm delivery"""
        self.confirmed = True

    def basic_publish(self, **kwargs):
        """badic publish"""
        self.published = kwargs


class FakeConnection:
    """class for fake connection"""
    def __init__(self, channel):
        self._channel = channel
        self.closed = False

    def channel(self):
        """define channel"""
        return self._channel

    def close(self):
        """define close"""
        self.closed = True

@pytest.mark.buttons
def test_open_channel_and_publish_task(monkeypatch):
    """test open channel"""
    fake_channel = FakeChannel()
    fake_connection = FakeConnection(fake_channel)
    captured = {}

    monkeypatch.setenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    monkeypatch.setattr(
        publisher.pika,
        "URLParameters",
        lambda url: captured.setdefault("url", url),
    )
    monkeypatch.setattr(
        publisher.pika,
        "BlockingConnection",
        lambda params: fake_connection,
    )

    publisher.publish_task("demo", payload={"x": 1}, headers={"h": "v"})

    body = json.loads(fake_channel.published["body"].decode("utf-8"))
    assert captured["url"] == "amqp://guest:guest@rabbitmq:5672/"
    assert fake_channel.exchange["exchange"] == "tasks"
    assert fake_channel.queue["queue"] == "tasks_q"
    assert body["kind"] == "demo"
    assert body["payload"] == {"x": 1}
    assert fake_channel.published["properties"].headers == {"h": "v"}
    assert fake_connection.closed is True
