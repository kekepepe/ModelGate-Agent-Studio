"""Provider factory for creating and managing model providers.

Supports two provider types:
  - mock: MockModelProvider (for testing/development)
  - openai: OpenAICompatibleProvider (for real API calls)

Configuration via environment variables or explicit set_provider().
"""

import os
from typing import Optional

from src.services.providers.base import ModelProvider
from src.services.providers.mock_provider import MockModelProvider


_provider: Optional[ModelProvider] = None


class ProviderConfigurationError(RuntimeError):
    """A requested execution mode has no usable provider configuration."""


def get_provider(model=None, execution_mode: Optional[str] = None) -> ModelProvider:
    """Return a provider for one model without silently falling back to Mock.

    A manually installed provider is reserved for tests and controlled runtime
    overrides. Live calls use the selected Model Manager record, not process
    global credentials, so two configured providers can coexist safely.
    """
    global _provider
    if _provider is not None:
        return _provider
    mode = (execution_mode or os.environ.get("EXECUTION_MODE", "live")).lower()
    if mode == "mock":
        return create_provider("mock")
    if mode not in {"live", "sandbox", "dry_run"}:
        raise ProviderConfigurationError(f"Unsupported execution mode: {mode}")
    if model is None:
        raise ProviderConfigurationError("No selected live model is available")
    if not getattr(model, "is_enabled", False):
        raise ProviderConfigurationError(f"Model '{getattr(model, 'display_name', model.id)}' is disabled")
    api_key = getattr(model, "api_key", None) or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ProviderConfigurationError(
            f"Live execution requires an API key for enabled model '{getattr(model, 'display_name', model.id)}'. "
            "Configure it in Model Manager or explicitly select Mock mode."
        )
    return create_provider("openai", api_key=api_key, base_url=getattr(model, "api_base_url", None))


def set_provider(provider: ModelProvider) -> None:
    """Replace the global provider instance (for testing or runtime switch)."""
    global _provider
    _provider = provider


def create_provider(provider_type: str, *, api_key: Optional[str] = None, base_url: Optional[str] = None) -> ModelProvider:
    """Create a new provider instance by type.

    Args:
        provider_type: "mock" or "openai"

    Returns:
        A ModelProvider instance.

    Raises:
        ValueError: if provider_type is unknown.
    """
    if provider_type == "mock":
        provider = MockModelProvider()
        _configure_mock_defaults(provider)
        return provider
    elif provider_type in {"openai", "openai_compatible", "anthropic", "deepseek", "kimi", "glm", "minimax"}:
        try:
            from src.services.providers.openai_compatible_provider import OpenAICompatibleProvider
            return OpenAICompatibleProvider(api_key=api_key, base_url=base_url)
        except ImportError:
            raise ValueError("OpenAI provider not available (install openai package)")
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def _configure_mock_defaults(provider: MockModelProvider) -> None:
    """Configure mock outputs for seeded models."""
    provider.configure_model(
        model_id="model-gpt-4-turbo",
        output_text_fn=lambda prompt, sys: (
            f"[GPT-4 Turbo Plan]\n"
            f"Analyzed goal and created task breakdown:\n"
            f"- Task 1: Core implementation\n"
            f"- Task 2: Review and testing\n\n"
            f"Estimated effort: moderate."
        ),
        input_tokens=200,
        output_tokens=300,
        latency_ms=600,
    )
    provider.configure_model(
        model_id="model-claude-opus",
        output_text_fn=lambda prompt, sys: (
            f"[Claude 3 Opus]\n"
            f"Executed coding task successfully.\n"
            f"```python\ndef solve():\n    # Implementation\n    return result\n```\n"
            f"All tests passing."
        ),
        input_tokens=250,
        output_tokens=400,
        latency_ms=800,
    )
    provider.configure_model(
        model_id="model-claude-3-haiku",
        output_text_fn=lambda prompt, sys: (
            f"[Claude 3 Haiku]\n"
            f"Summary generated.\n"
            f"Key findings: task completed with expected quality."
        ),
        input_tokens=150,
        output_tokens=200,
        latency_ms=300,
    )
    provider.configure_model(
        model_id="model-deepseek-coder",
        output_text_fn=lambda prompt, sys: (
            f"[DeepSeek Coder]\n"
            f"Generated implementation:\n"
            f"```typescript\nfunction main() {{\n  // solution\n}}\n```"
        ),
        input_tokens=200,
        output_tokens=350,
        latency_ms=500,
    )
