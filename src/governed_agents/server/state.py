"""Tiny SQLite store for the order ledger + approval coordination.

Why SQLite and not Kafka for approvals? Approvals need synchronous lookup from
a second process (the approver CLI). SQLite is one stdlib import and zero
operational overhead. All *audit-visible* state still flows through Kafka.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from ..config import SETTINGS

DB_PATH = SETTINGS.state_dir / "demo.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'placed',
    flagged INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    identity TEXT NOT NULL,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    approver TEXT,
    decided_at TEXT
);
"""


def init_db() -> None:
    with _conn() as c:
        c.executescript(_SCHEMA)


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_order(order: dict) -> None:
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO orders (order_id, customer_id, payload, status) VALUES (?, ?, ?, ?)",
            (order["order_id"], order["customer_id"], json.dumps(order), order.get("status", "placed")),
        )


def list_recent_orders(customer_id: str, limit: int = 5) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT payload, status, flagged FROM orders WHERE customer_id=? ORDER BY rowid DESC LIMIT ?",
            (customer_id, limit),
        ).fetchall()
    out = []
    for r in rows:
        o = json.loads(r["payload"])
        o["status"] = r["status"]
        o["flagged"] = bool(r["flagged"])
        out.append(o)
    return out


def get_order(order_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute(
            "SELECT payload, status, flagged FROM orders WHERE order_id=?", (order_id,)
        ).fetchone()
    if not row:
        return None
    o = json.loads(row["payload"])
    o["status"] = row["status"]
    o["flagged"] = bool(row["flagged"])
    return o


def flag_order(order_id: str) -> bool:
    with _conn() as c:
        cur = c.execute("UPDATE orders SET flagged=1 WHERE order_id=?", (order_id,))
        return cur.rowcount > 0


def set_status(order_id: str, status: str) -> bool:
    with _conn() as c:
        cur = c.execute("UPDATE orders SET status=? WHERE order_id=?", (status, order_id))
        return cur.rowcount > 0


def create_approval(approval_id: str, identity: str, tool: str, args: dict) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO approvals (approval_id, identity, tool, args) VALUES (?, ?, ?, ?)",
            (approval_id, identity, tool, json.dumps(args)),
        )


def get_approval(approval_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute(
            "SELECT approval_id, identity, tool, args, status, approver, decided_at FROM approvals WHERE approval_id=?",
            (approval_id,),
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["args"] = json.loads(d["args"])
    return d


def decide_approval(approval_id: str, status: str, approver: str, decided_at: str) -> bool:
    with _conn() as c:
        cur = c.execute(
            "UPDATE approvals SET status=?, approver=?, decided_at=? WHERE approval_id=? AND status='pending'",
            (status, approver, decided_at, approval_id),
        )
        return cur.rowcount > 0


def list_pending_approvals() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT approval_id, identity, tool, args FROM approvals WHERE status='pending' ORDER BY rowid"
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["args"] = json.loads(d["args"])
        out.append(d)
    return out
