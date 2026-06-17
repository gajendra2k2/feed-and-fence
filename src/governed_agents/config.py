from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    offline_mode: bool
    anthropic_api_key: str
    kafka_bootstrap: str
    mcp_host: str
    mcp_port: int
    state_dir: Path
    policy_path: Path


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    state_dir = Path(os.getenv("STATE_DIR", "./state")).resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    policy_path = Path(__file__).parent / "policy.yaml"
    return Settings(
        offline_mode=_bool("OFFLINE_MODE", False),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        kafka_bootstrap=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
        mcp_host=os.getenv("MCP_HOST", "127.0.0.1"),
        mcp_port=int(os.getenv("MCP_PORT", "8000")),
        state_dir=state_dir,
        policy_path=policy_path,
    )


SETTINGS = load_settings()
