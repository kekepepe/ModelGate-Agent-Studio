from src.services.providers.provider_config import (
    execution_mode,
    provider_api_base,
    provider_api_key,
    provider_model_name,
)


def test_environment_overrides_database_provider_configuration(monkeypatch):
    monkeypatch.setenv("PROVIDER_API_BASE", "https://env-provider.test/v1")
    monkeypatch.setenv("PROVIDER_API_KEY", "env-secret")
    monkeypatch.setenv("PLANNER_MODEL_NAME", "planner-real-name")
    monkeypatch.setenv("MODEL_GATE_EXECUTION_MODE", "REAL")

    assert provider_api_base("https://database.test/v1") == "https://env-provider.test/v1"
    assert provider_api_key("database-secret") == "env-secret"
    assert provider_model_name("planner", "database-model") == "planner-real-name"
    assert execution_mode("mock") == "real"


def test_database_model_name_is_used_without_role_override(monkeypatch):
    for name in ("PLANNER_MODEL_NAME", "WORKER_MODEL_NAME", "VERIFIER_MODEL_NAME"):
        monkeypatch.delenv(name, raising=False)
    assert provider_model_name("coder", "provider-model") == "provider-model"


def test_database_provider_key_is_ignored_without_environment_secret(monkeypatch):
    monkeypatch.delenv("PROVIDER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert provider_api_key("legacy-plaintext-secret") is None
