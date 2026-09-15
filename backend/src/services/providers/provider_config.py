"""Live provider configuration: per-model credentials first, env fallback.

V1.3 D3: real multi-provider requires per-model credentials (each provider
has its own key/base_url), so the Model row is now the primary source and
the process env is the fallback for legacy env-first deployments. Keys live
in the local SQLite file — the same trust boundary as the workspace files
themselves (single-machine, single-developer product) — and are redacted
everywhere they could reach a log or API response.
"""

import os
from typing import Optional


ROLE_MODEL_ENV = {
    "planner": "PLANNER_MODEL_NAME",
    "coder": "WORKER_MODEL_NAME",
    "research": "WORKER_MODEL_NAME",
    "summarizer": "WORKER_MODEL_NAME",
    "reviewer": "VERIFIER_MODEL_NAME",
    "supervisor": "VERIFIER_MODEL_NAME",
    "verification": "VERIFIER_MODEL_NAME",
}


def provider_api_key(database_value: Optional[str] = None) -> Optional[str]:
    """Per-model key first, env fallback. None means 'no credential anywhere'
    — callers must raise an explicit configuration error, never fall back to
    mock silently."""
    if database_value:
        return database_value
    return os.environ.get("PROVIDER_API_KEY") or os.environ.get("OPENAI_API_KEY")


def provider_api_base(database_value: Optional[str] = None) -> Optional[str]:
    """Per-model base_url first (each provider has its own endpoint), env
    fallback for legacy env-first deployments."""
    if database_value:
        return database_value
    return os.environ.get("PROVIDER_API_BASE") or os.environ.get("OPENAI_BASE_URL")


def provider_model_name(role: str, database_value: str) -> str:
    env_name = ROLE_MODEL_ENV.get(role)
    return (os.environ.get(env_name) if env_name else None) or database_value


def execution_mode(default: str = "live") -> str:
    return (os.environ.get("MODEL_GATE_EXECUTION_MODE") or os.environ.get("EXECUTION_MODE") or default).lower()
