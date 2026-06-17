"""Multi-model routing — concrete version of 'scalable multi-model architecture'.

Decide which model to ask based on signal in the request, log the decision,
return the result. The decision itself is auditable — that's the point.
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import llm
from . import state


@dataclass
class RoutingDecision:
    model: str
    tier_label: str
    reason: str


def _customer_risk_signal(customer_id: str) -> tuple[float, dict]:
    orders = state.list_recent_orders(customer_id, limit=20)
    if not orders:
        return 0.0, {"order_count": 0}
    total = sum(o.get("amount", 0) for o in orders)
    countries = {o.get("country") for o in orders}
    high_value = sum(1 for o in orders if o.get("amount", 0) > 200)
    score = min(1.0, (total / 2000) + (0.2 if len(countries) > 2 else 0) + (0.1 * high_value))
    return score, {
        "order_count": len(orders),
        "total_spend": round(total, 2),
        "distinct_countries": len(countries),
        "high_value_orders": high_value,
    }


def route(customer_id: str) -> tuple[RoutingDecision, dict, llm.LLMResult]:
    score, signals = _customer_risk_signal(customer_id)
    if score < 0.3:
        decision = RoutingDecision(llm.MODEL_HAIKU, "low", f"risk_score={score:.2f} — cheap model is enough")
    elif score < 0.7:
        decision = RoutingDecision(llm.MODEL_SONNET, "medium", f"risk_score={score:.2f} — mid-tier model")
    else:
        decision = RoutingDecision(llm.MODEL_OPUS, "high", f"risk_score={score:.2f} — escalate to flagship model")

    prompt = (
        f"Customer {customer_id} recent activity: {signals}. "
        "In two sentences, assess fraud risk and recommend an action."
    )
    result = llm.assess(decision.model, prompt)
    return decision, signals, result
