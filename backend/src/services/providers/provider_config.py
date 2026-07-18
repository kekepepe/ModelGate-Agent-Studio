"""Environment-first live provider configuration without persisting secrets."""

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
    """Resolve credentials from the process secret store only.

    ``database_value`` remains in the signature for compatibility with legacy
    rows, but is deliberately ignored so plaintext database credentials cannot
    silently become a production secret source.
    """
    _ = database_value
    return os.environ.get("PROVIDER_API_KEY") or os.environ.get("OPENAI_API_KEY")


def provider_api_base(database_value: Optional[str] = None) -> Optional[str]:
    return os.environ.get("PROVIDER_API_BASE") or os.environ.get("OPENAI_BASE_URL") or database_value


def provider_model_name(role: str, database_value: str) -> str:
    env_name = ROLE_MODEL_ENV.get(role)
    return (os.environ.get(env_name) if env_name else None) or database_value


def execution_mode(default: str = "live") -> str:
    return (os.environ.get("MODEL_GATE_EXECUTION_MODE") or os.environ.get("EXECUTION_MODE") or default).lower()
