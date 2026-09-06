"""LLMProvider protocol — the single contract every provider must satisfy.

Per `docs/design/2026-09-06-platform-redesign.md` §6.5:
- Business code calls these methods only.
- Provider implementations may use any underlying SDK (LiteLLM, raw HTTP, etc.).
- Token counting is a best-effort estimate; do not rely on it for billing.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterable, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """The only interface the rest of the codebase is allowed to depend on."""

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str,
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return a normalized chat completion dict.

        Shape (minimum required keys):
            {
                "id": str,
                "model": str,
                "choices": [{"index": int, "message": {"role": "assistant", "content": str | None, "tool_calls": list | None}, "finish_reason": str}],
                "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
            }
        """
        ...

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model: str,
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield streaming chunks. Each chunk is a dict with the same shape as
        `chat()`'s response, but partial — typically `choices[0].delta` instead
        of `choices[0].message`."""
        ...

    def token_count(self, messages: Iterable[dict[str, Any]], model: str | None = None) -> int:
        """Return a best-effort token estimate. Used for budget guards and
        handoff threshold checks, not for billing."""
        ...


# ---------------------------------------------------------------------------
# Error hierarchy (per design §6.6)
# ---------------------------------------------------------------------------

class ProviderError(Exception):
    """Base class for all provider-layer errors."""

    code: str = "provider_error"

    def __init__(self, message: str, *, code: str | None = None, cause: Exception | None = None):
        super().__init__(message)
        if code:
            self.code = code
        self.__cause__ = cause


class ProviderAuthError(ProviderError):
    code = "provider_auth_error"


class ProviderRateLimit(ProviderError):
    code = "provider_rate_limited"


class ProviderTimeout(ProviderError):
    code = "provider_timeout"


class ProviderContextOverflow(ProviderError):
    code = "provider_context_overflow"


class ProviderInvalidResponse(ProviderError):
    code = "provider_invalid_response"


class QuotaExhausted(ProviderError):
    code = "quota_exhausted"
