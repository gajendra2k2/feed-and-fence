"""Shadow mode — simulate a write, return the would-be effect, do not commit.

The agent gets a structurally identical response. It cannot tell the difference.
That's the point: shadow mode lets you validate a high-risk agent capability in
production traffic before turning execution on.
"""
from __future__ import annotations

from typing import Any

from . import state


def cancel_order_shadow(order_id: str, reason: str) -> dict[str, Any]:
    order = state.get_order(order_id)
    if not order:
        return {"shadow": True, "would_apply": False, "reason_unmet": "order not found"}
    return {
        "shadow": True,
        "would_apply": True,
        "order_id": order_id,
        "current_status": order["status"],
        "would_become_status": "cancelled",
        "would_refund_amount": order.get("amount"),
        "agent_reason": reason,
    }
