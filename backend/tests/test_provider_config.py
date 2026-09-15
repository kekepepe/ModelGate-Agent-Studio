
from src.services.providers.provider_config import (
    execution_mode,
    provider_api_base,
    provider_api_key,
    provider_model_name,
)


def test_environment_overrides_database_provider_configuration(monkeypatch):
    monkeypatch.setenv("PROVIDER_API_BASE", "https://env-provider.test/v1")
    monkeypatch.setenv("PLANNER_MODEL_NAME", "planner-real-name")
    monkeypatch.setenv("MODEL_GATE_EXECUTION_MODE", "REAL")

    # V1.3 D3: the model row is now the primary source (per-model credentials
    # are what makes real multi-provider possible); env is the fallback.
    assert provider_api_base("https://database.test/v1") == "https://database.test/v1"
    assert provider_api_key("database-secret") == "database-secret"
    assert provider_model_name("planner", "database-model") == "planner-real-name"
    assert execution_mode("mock") == "real"


def test_database_model_name_is_used_without_role_override(monkeypatch):
    for name in ("PLANNER_MODEL_NAME", "WORKER_MODEL_NAME", "VERIFIER_MODEL_NAME"):
        monkeypatch.delenv(name, raising=False)
    assert provider_model_name("coder", "provider-model") == "provider-model"


def test_environment_fallback_when_model_row_has_no_credential(monkeypatch):
    """Legacy env-first deployments keep working: a model row without an
    api_key still picks up PROVIDER_API_KEY / OPENAI_API_KEY."""
    monkeypatch.setenv("PROVIDER_API_KEY", "env-secret")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert provider_api_key(None) == "env-secret"

    monkeypatch.delenv("PROVIDER_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    assert provider_api_key(None) == "openai-secret"


def test_no_credential_anywhere_returns_none(monkeypatch):
    monkeypatch.delenv("PROVIDER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert provider_api_key(None) is None
    # Callers turn None into an explicit ProviderConfigurationError — a live
    # deployment without a key must fail loudly, never silently mock.


def test_base_url_prefers_model_row_then_env(monkeypatch):
    monkeypatch.setenv("PROVIDER_API_BASE", "https://env-provider.test/v1")
    assert provider_api_base("https://database.test/v1") == "https://database.test/v1"
    assert provider_api_base(None) == "https://env-provider.test/v1"

    monkeypatch.delenv("PROVIDER_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    assert provider_api_base(None) is None
