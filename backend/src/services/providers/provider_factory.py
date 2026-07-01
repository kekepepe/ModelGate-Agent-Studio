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


def get_provider() -> ModelProvider:
    """Get the current global provider instance."""
    global _provider
    if _provider is None:
        provider_type = os.environ.get("MODEL_PROVIDER", "mock")
        _provider = create_provider(provider_type)
    return _provider


def set_provider(provider: ModelProvider) -> None:
    """Replace the global provider instance (for testing or runtime switch)."""
    global _provider
    _provider = provider


def create_provider(provider_type: str) -> ModelProvider:
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
    elif provider_type == "openai":
        try:
            from src.services.providers.openai_compatible_provider import OpenAICompatibleProvider
            return OpenAICompatibleProvider()
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
