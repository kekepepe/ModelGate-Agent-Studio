"""LiteLLM-backed provider (per design §6.5).

Reads PROVIDER_API_BASE / PROVIDER_API_KEY / PROVIDER_TIMEOUT_SECONDS from
the environment (see `core/config.py`). Compatible with any OpenAI-style
endpoint (OpenAI, Anthropic via gateway, DeepSeek, Moonshot, Zhipu, etc.).

Design rules respected:
- All litellm calls happen inside this module. The rest of the codebase
  must not `import litellm` directly.
- Provider errors are normalized to `ProviderError` subclasses from `base.py`.
- Streaming and non-streaming share the same `_call_kwargs()` helper.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, AsyncIterator, Iterable

import litellm

from .base import (
    LLMProvider,
    ProviderAuthError,
    ProviderContextOverflow,
    ProviderError,
    ProviderInvalidResponse,
    ProviderRateLimit,
    ProviderTimeout,
)

logger = logging.getLogger(__name__)

# Tell litellm to be quiet about provider quirks we already handle.
litellm.suppress_debug_info = True


class LiteLLMProvider:
    """LiteLLM-backed implementation of `LLMProvider`."""

    def __init__(
        self,
        *,
        api_base: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_base = api_base or os.getenv("PROVIDER_API_BASE", "")
        self.api_key = api_key if api_key is not None else os.getenv("PROVIDER_API_KEY", "")
        self.timeout = timeout or int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "60"))

        if not self.api_key:
            logger.warning(
                "LiteLLMProvider initialised without PROVIDER_API_KEY. "
                "Real LLM calls will fail until the env var is set."
            )

    # ------------------------------------------------------------------
    # Public API (matches LLMProvider protocol)
    # ------------------------------------------------------------------

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
        call_kwargs = self._call_kwargs(
            tools=tools, temperature=temperature, max_tokens=max_tokens, **kwargs
        )
        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                api_base=self.api_base or None,
                api_key=self.api_key or None,
                timeout=self.timeout,
                **call_kwargs,
            )
        except litellm.AuthenticationError as exc:
            raise ProviderAuthError(f"auth failed: {exc}", cause=exc) from exc
        except litellm.RateLimitError as exc:
            raise ProviderRateLimit(f"rate limited: {exc}", cause=exc) from exc
        except litellm.Timeout as exc:
            raise ProviderTimeout(f"timeout after {self.timeout}s: {exc}", cause=exc) from exc
        except litellm.ContextWindowExceededError as exc:
            raise ProviderContextOverflow(
                f"context overflow: {exc}", cause=exc
            ) from exc
        except litellm.BadRequestError as exc:
            raise ProviderInvalidResponse(f"bad request: {exc}", cause=exc) from exc
        except litellm.APIError as exc:
            raise ProviderError(f"provider api error: {exc}", cause=exc) from exc

        return self._normalize_response(response, model=model)

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
        call_kwargs = self._call_kwargs(
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                api_base=self.api_base or None,
                api_key=self.api_key or None,
                timeout=self.timeout,
                **call_kwargs,
            )
            async for chunk in response:
                yield self._normalize_stream_chunk(chunk, model=model)
        except litellm.AuthenticationError as exc:
            raise ProviderAuthError(f"auth failed: {exc}", cause=exc) from exc
        except litellm.RateLimitError as exc:
            raise ProviderRateLimit(f"rate limited: {exc}", cause=exc) from exc
        except litellm.Timeout as exc:
            raise ProviderTimeout(f"timeout after {self.timeout}s: {exc}", cause=exc) from exc
        except litellm.ContextWindowExceededError as exc:
            raise ProviderContextOverflow(
                f"context overflow: {exc}", cause=exc
            ) from exc
        except litellm.BadRequestError as exc:
            raise ProviderInvalidResponse(f"bad request: {exc}", cause=exc) from exc
        except litellm.APIError as exc:
            raise ProviderError(f"provider api error: {exc}", cause=exc) from exc

    def token_count(
        self, messages: Iterable[dict[str, Any]], model: str | None = None
    ) -> int:
        """Best-effort token count. Uses litellm's counter if available,
        otherwise falls back to a 4-chars-per-token estimate."""
        try:
            return litellm.token_counter(
                model=model or "gpt-3.5-turbo", messages=list(messages)
            )
        except Exception:
            return sum(
                len(str(m.get("content") or "")) for m in messages
            ) // 4

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _call_kwargs(
        self,
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **extras: Any,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if tools is not None:
            kwargs["tools"] = tools
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        kwargs.update(extras)
        return kwargs

    def _normalize_response(
        self, response: Any, *, model: str
    ) -> dict[str, Any]:
        """Coerce whatever litellm returned into our normalized shape."""
        # `response` is a litellm ModelResponse (pydantic). Access via .model_dump
        # to avoid touching vendor internals.
        if hasattr(response, "model_dump"):
            data = response.model_dump()
        elif hasattr(response, "dict"):
            data = response.dict()
        else:
            data = dict(response)
        # Guarantee required keys
        data.setdefault("id", "")
        data.setdefault("model", model)
        data.setdefault("choices", [])
        return data

    def _normalize_stream_chunk(self, chunk: Any, *, model: str) -> dict[str, Any]:
        if hasattr(chunk, "model_dump"):
            data = chunk.model_dump()
        elif hasattr(chunk, "dict"):
            data = chunk.dict()
        else:
            data = dict(chunk)
        data.setdefault("model", model)
        data.setdefault("choices", [])
        return data
