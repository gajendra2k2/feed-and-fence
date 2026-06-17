"""Tests that don't need Kafka — verifies policy + identity logic.

Run with `pytest -q tests/` after `pip install -e '.[dev]'`.
"""
from __future__ import annotations

import pytest

from governed_agents.server import identity


def test_viewer_can_read():
    tp = identity.check("viewer", "list_recent_orders")
    assert tp.tier == 1


def test_viewer_cannot_write():
    with pytest.raises(identity.AccessDenied):
        identity.check("viewer", "flag_order_for_review")


def test_basic_agent_blocked_from_tier3():
    with pytest.raises(identity.AccessDenied):
        identity.check("agent_basic", "cancel_order")


def test_advanced_agent_can_do_everything():
    for tool in ("list_recent_orders", "flag_order_for_review", "cancel_order", "issue_refund"):
        tp = identity.check("agent_advanced", tool)
        assert tp.tier >= 1


def test_unknown_identity_denied():
    with pytest.raises(identity.AccessDenied):
        identity.check("ghost", "list_recent_orders")


def test_cancel_order_marked_shadow_by_default():
    tp = identity.check("agent_advanced", "cancel_order")
    assert tp.shadow_by_default is True


def test_issue_refund_marked_approval_required():
    tp = identity.check("agent_advanced", "issue_refund")
    assert tp.approval_required is True
