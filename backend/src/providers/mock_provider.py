"""Mock provider for development and tests (per design §6.5).

Echoes the last user message back as a structured response. Never makes
a network call. Set MODEL_GATE_EXECUTION_MODE=mock to activate.

NOT for production. Production must use a real provider with a configured
API key; an empty key is the loudest possible failure mode (per design).
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, AsyncIterator, Iterable


class MockProvider:
    """Deterministic-ish echo provider. No external dependencies."""

    def __init__(self, *, latency_seconds: float = 0.05) -> None:
        self.latency_seconds = latency_seconds

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
        await asyncio.sleep(self.latency_seconds)
        prompt = self._last_user_text(messages)
        reply = self._format_reply(model, prompt)
        return {
            "id": f"mock-{uuid.uuid4().hex[:8]}",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": reply},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": self._estimate_tokens(messages),
                "completion_tokens": self._estimate_tokens(reply),
                "total_tokens": self._estimate_tokens(messages) + self._estimate_tokens(reply),
            },
        }

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
        prompt = self._last_user_text(messages)
        reply = self._format_reply(model, prompt)
        words = reply.split(" ")
        for i, word in enumerate(words):
            await asyncio.sleep(self.latency_seconds / max(len(words), 1))
            chunk = {
                "id": f"mock-{uuid.uuid4().hex[:8]}",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": word + " "},
                        "finish_reason": "stop" if i == len(words) - 1 else None,
                    }
                ],
            }
            yield chunk

    def token_count(
        self, messages: Iterable[dict[str, Any]], model: str | None = None
    ) -> int:
        return self._estimate_tokens(list(messages))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _last_user_text(messages: list[dict[str, Any]]) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                content = m.get("content")
                return content if isinstance(content, str) else str(content)
        return ""

    @staticmethod
    def _format_reply(model: str, prompt: str) -> str:
        snippet = (prompt or "").strip().splitlines()[0] if prompt else "(empty)"
        if len(snippet) > 120:
            snippet = snippet[:120] + "..."
        return (
            f"[Mock {model}] Received goal. "
            f"First line: \"{snippet}\". "
            f"This is a deterministic mock response. "
            f"Set MODEL_GATE_EXECUTION_MODE=live and PROVIDER_API_KEY to use a real model."
        )

    @staticmethod
    def _estimate_tokens(messages_or_text: Any) -> int:
        if isinstance(messages_or_text, str):
            return len(messages_or_text) // 4
        # iterable of message dicts
        total = 0
        for m in messages_or_text:
            content = m.get("content") if isinstance(m, dict) else None
            if isinstance(content, str):
                total += len(content) // 4
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        total += len(str(part.get("text", ""))) // 4
        return total
