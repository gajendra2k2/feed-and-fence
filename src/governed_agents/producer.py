"""Synthetic e-commerce order stream producer.

Run with: `make producer` (or `python -m governed_agents.producer`).
Streams a steady trickle of orders into the `orders` Kafka topic so the agent
has live data to read. Keep this running in its own terminal during the demo.
"""
from __future__ import annotations

import json
import random
import signal
import time
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer

from .config import SETTINGS
from .topics import ORDERS

CUSTOMERS = [f"C{i:03d}" for i in range(1, 21)]
ITEMS = [
    ("SKU-001", "Wireless Mouse", 29.99),
    ("SKU-002", "Mechanical Keyboard", 119.00),
    ("SKU-003", "27\" Monitor", 349.00),
    ("SKU-004", "USB-C Hub", 49.50),
    ("SKU-005", "Noise-Canceling Headphones", 279.00),
    ("SKU-006", "Webcam 1080p", 89.00),
    ("SKU-007", "Desk Lamp", 39.00),
    ("SKU-008", "Standing Desk Mat", 59.99),
]
COUNTRIES = ["US", "CA", "GB", "DE", "IN", "JP"]


def _build_order() -> dict:
    customer = random.choice(CUSTOMERS)
    item = random.choice(ITEMS)
    qty = random.randint(1, 3)
    return {
        "order_id": f"O-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": customer,
        "ts": datetime.now(timezone.utc).isoformat(),
        "sku": item[0],
        "name": item[1],
        "qty": qty,
        "amount": round(item[2] * qty, 2),
        "country": random.choice(COUNTRIES),
        "status": "placed",
    }


def main() -> None:
    producer = Producer({"bootstrap.servers": SETTINGS.kafka_bootstrap, "client.id": "orders-producer"})
    running = {"v": True}

    def _stop(*_a):
        running["v"] = False
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    print(f"[producer] streaming to topic '{ORDERS}' at {SETTINGS.kafka_bootstrap} (Ctrl+C to stop)")
    n = 0
    while running["v"]:
        order = _build_order()
        producer.produce(ORDERS, key=order["customer_id"].encode(), value=json.dumps(order).encode())
        producer.poll(0)
        n += 1
        if n % 10 == 0:
            print(f"[producer] {n} orders sent — latest {order['order_id']} ${order['amount']}")
        time.sleep(random.uniform(0.4, 1.2))
    producer.flush(5)
    print(f"[producer] stopped after {n} orders")


if __name__ == "__main__":
    main()
