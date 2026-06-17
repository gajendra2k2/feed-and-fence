"""Audit log — every tool call as a structured event on a Kafka topic.

The auditor IS a stream. That's the bridge from Part 1 (lineage) to Part 2
(auditability) in the talk. The audit viewer (`scripts/audit_viewer.py`) is a
plain Kafka consumer; anyone can subscribe.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from confluent_kafka import Producer

from ..config import SETTINGS
from ..topics import AUDIT

_producer = Producer({"bootstrap.servers": SETTINGS.kafka_bootstrap, "client.id": "audit-writer"})


def emit(
    *,
    identity: str,
    tool: str,
    tier: int,
    outcome: str,
    args: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    detail: str | None = None,
) -> str:
    event = {
        "event_id": uuid.uuid4().hex,
        "ts": datetime.now(timezone.utc).isoformat(),
        "identity": identity,
        "tool": tool,
        "tier": tier,
        "outcome": outcome,
        "args": args or {},
        "result": result or {},
        "detail": detail,
    }
    _producer.produce(AUDIT, key=identity.encode(), value=json.dumps(event).encode())
    _producer.poll(0)
    return event["event_id"]


def flush() -> None:
    _producer.flush(2)
