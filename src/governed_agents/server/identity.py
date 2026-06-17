"""Identity + policy enforcement — the trust boundary.

The model is untrusted. The server holds policy, the server denies. This module
loads `policy.yaml` and answers one question: may `identity` call `tool`?
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..config import SETTINGS


@dataclass(frozen=True)
class ToolPolicy:
    tier: int
    shadow_by_default: bool = False
    approval_required: bool = False
    multi_model: bool = False


@dataclass(frozen=True)
class Policy:
    identities: dict[str, list[int]]
    tools: dict[str, ToolPolicy]


def _load(path: Path) -> Policy:
    raw = yaml.safe_load(path.read_text())
    identities = {name: list(spec["allowed_tiers"]) for name, spec in raw["identities"].items()}
    tools = {
        name: ToolPolicy(
            tier=int(spec["tier"]),
            shadow_by_default=bool(spec.get("shadow_by_default", False)),
            approval_required=bool(spec.get("approval_required", False)),
            multi_model=bool(spec.get("multi_model", False)),
        )
        for name, spec in raw["tools"].items()
    }
    return Policy(identities=identities, tools=tools)


POLICY = _load(SETTINGS.policy_path)


class AccessDenied(Exception):
    pass


def check(identity: str, tool: str) -> ToolPolicy:
    if identity not in POLICY.identities:
        raise AccessDenied(f"unknown identity '{identity}'")
    if tool not in POLICY.tools:
        raise AccessDenied(f"unknown tool '{tool}'")
    tp = POLICY.tools[tool]
    if tp.tier not in POLICY.identities[identity]:
        raise AccessDenied(
            f"identity '{identity}' not authorized for tier-{tp.tier} tool '{tool}'"
        )
    return tp
