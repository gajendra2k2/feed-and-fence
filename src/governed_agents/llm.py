"""Thin LLM wrapper used only by the Beat-6 multi-model routing demo.

When OFFLINE_MODE=true (or no API key set), returns canned responses so the
demo runs without internet. The Beats 1–5 governance flow never calls an LLM.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import SETTINGS

MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS = "claude-opus-4-7"


@dataclass
class LLMResult:
    model: str
    text: str
    offline: bool


def _canned(model: str, prompt: str) -> str:
    if model == MODEL_HAIKU:
        return "Low risk. Pattern matches typical purchasing behavior."
    if model == MODEL_SONNET:
        return "Moderate risk. Velocity and geo spread warrant a soft flag."
    return (
        "High risk. Concentrated high-value orders across mismatched billing/shipping "
        "geos within a short window — recommend manual review before any payout."
    )


def assess(model: str, prompt: str) -> LLMResult:
    if SETTINGS.offline_mode or not SETTINGS.anthropic_api_key:
        return LLMResult(model=model, text=_canned(model, prompt), offline=True)
    from anthropic import Anthropic
    client = Anthropic(api_key=SETTINGS.anthropic_api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return LLMResult(model=model, text=text.strip(), offline=False)
