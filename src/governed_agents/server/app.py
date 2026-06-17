"""FastMCP server — the governance surface.

Exposes six tools via streamable HTTP. Also runs a background thread that
consumes the `orders` Kafka stream into the local order ledger so the agent's
read tools see fresh data.
"""
from __future__ import annotations

import json
import threading

from confluent_kafka import Consumer
from fastmcp import FastMCP

from ..config import SETTINGS
from ..topics import ORDERS
from . import state, tools

mcp = FastMCP("governed-agents")


@mcp.tool
def list_recent_orders(identity: str, customer_id: str) -> dict:
    """Return the most recent orders for a customer. Tier 1 (read)."""
    return tools.list_recent_orders(identity, customer_id)


@mcp.tool
def get_order_details(identity: str, order_id: str) -> dict:
    """Return full details for one order. Tier 1 (read)."""
    return tools.get_order_details(identity, order_id)


@mcp.tool
def flag_order_for_review(identity: str, order_id: str, reason: str) -> dict:
    """Flag an order for human review. Tier 2 (low-risk write)."""
    return tools.flag_order_for_review(identity, order_id, reason)


@mcp.tool
def cancel_order(identity: str, order_id: str, reason: str) -> dict:
    """Cancel an order. Tier 3 — runs in shadow mode by default."""
    return tools.cancel_order(identity, order_id, reason)


@mcp.tool
def issue_refund(identity: str, order_id: str, amount: float, approval_id: str | None = None) -> dict:
    """Issue a refund. Tier 4 — requires human approval (two-step)."""
    return tools.issue_refund(identity, order_id, amount, approval_id)


@mcp.tool
def check_approval(identity: str, approval_id: str) -> dict:
    """Check the status of a pending approval."""
    return tools.check_approval(identity, approval_id)


@mcp.tool
def assess_fraud_risk(identity: str, customer_id: str) -> dict:
    """Assess fraud risk for a customer. Routes between Haiku/Sonnet/Opus by signal."""
    return tools.assess_fraud_risk(identity, customer_id)


def _consume_orders() -> None:
    consumer = Consumer({
        "bootstrap.servers": SETTINGS.kafka_bootstrap,
        "group.id": "orders-ingest-server",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    consumer.subscribe([ORDERS])
    print(f"[server] consuming '{ORDERS}' → order ledger")
    try:
        while True:
            msg = consumer.poll(0.5)
            if msg is None or msg.error():
                continue
            try:
                order = json.loads(msg.value())
                state.upsert_order(order)
            except Exception as e:
                print(f"[server] bad order event: {e}")
    finally:
        consumer.close()


def main() -> None:
    state.init_db()
    t = threading.Thread(target=_consume_orders, daemon=True)
    t.start()
    print(f"[server] FastMCP on http://{SETTINGS.mcp_host}:{SETTINGS.mcp_port}/mcp")
    print(f"[server] offline_mode={SETTINGS.offline_mode}  kafka={SETTINGS.kafka_bootstrap}")
    mcp.run(transport="streamable-http", host=SETTINGS.mcp_host, port=SETTINGS.mcp_port)


if __name__ == "__main__":
    main()
