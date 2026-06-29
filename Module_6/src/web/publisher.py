"""RabbitMQ task publisher"""
import os
import json
from datetime import datetime
import pika

EXCHANGE = "tasks" #a durable direct exchange named tasks
QUEUE = "tasks_q" #a durable queue named tasks_q
ROUTING_KEY = "tasks" #a binding with routing key tasks

def _open_channel():
    """
    Reads: RABBITMQ_URL from the environment.
    Creates a connection (BlockingConnection) and channel.
    Declares (idempotent)
    Returns: the (connection, channel) pair.
    """
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)

    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Durable exchange & queue; bind once per process (idempotent)
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    ch.confirm_delivery()

    return conn, ch

def publish_task(kind: str, payload: dict | None = None,
headers: dict | None = None) -> None:
    """Publish a durable task message to RabbitMQ."""
    body = json.dumps(
        {
            "kind": kind,
            "ts": datetime.utcnow().isoformat(),
            "payload": payload or {},
        },
        separators=(",", ":"),
    ).encode("utf-8")

    conn, ch = _open_channel()

    try:
        ch.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,
                headers=headers or {},
            ),
            mandatory=True,
        )
    finally:
        conn.close()
