"""Mock model provider for testing and development.

Implements the ModelProvider protocol with configurable fake outputs,
token counts, and latency. Records call history for test assertions.
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Dict, Optional

from src.services.providers.base import ModelRequest, ModelResponse, ModelStreamEvent


@dataclass
class _ModelConfig:
    output_text: Optional[str] = None
    output_text_fn: Optional[Callable[[str, Optional[str]], str]] = None
    input_tokens: Optional[int] = None
    input_tokens_fn: Optional[Callable[[str], int]] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    tool_calls: Optional[list] = None
    raise_error: Optional[str] = None


class MockModelProvider:
    """Mock provider that simulates model API calls."""

    def __init__(self, default_latency_ms: int = 500, default_output_tokens: int = 200):
        self._configs: Dict[str, _ModelConfig] = {}
        self._default_latency_ms = default_latency_ms
        self._default_output_tokens = default_output_tokens
        self._call_history: list = []

    def configure_model(
        self,
        model_id: str,
        output_text: Optional[str] = None,
        output_text_fn: Optional[Callable[[str, Optional[str]], str]] = None,
        input_tokens: Optional[int] = None,
        input_tokens_fn: Optional[Callable[[str], int]] = None,
        output_tokens: Optional[int] = None,
        latency_ms: Optional[int] = None,
        tool_calls: Optional[list] = None,
        raise_error: Optional[str] = None,
    ) -> None:
        self._configs[model_id] = _ModelConfig(
            output_text=output_text,
            output_text_fn=output_text_fn,
            input_tokens=input_tokens,
            input_tokens_fn=input_tokens_fn,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
            raise_error=raise_error,
        )

    async def generate(self, request: ModelRequest) -> ModelResponse:
        config = self._configs.get(request.model)
        model_id = request.model

        if config and config.raise_error:
            raise RuntimeError(config.raise_error)

        if config and config.latency_ms is not None:
            latency_ms = config.latency_ms
        else:
            latency_ms = self._default_latency_ms + random.randint(-100, 100)

        await asyncio.sleep(latency_ms / 1000.0)

        prompt = request.messages[-1]["content"] if request.messages else ""
        system_prompt = next((m["content"] for m in request.messages if m.get("role") == "system"), None)

        if config and config.output_text_fn:
            output = config.output_text_fn(prompt, system_prompt)
        elif config and config.output_text:
            output = config.output_text
        else:
            output = self._default_output(prompt, model_id, system_prompt)

        if config and config.input_tokens_fn:
            input_tokens = config.input_tokens_fn(prompt)
        elif config and config.input_tokens is not None:
            input_tokens = config.input_tokens
        else:
            input_tokens = max(len(prompt) // 4, 50)

        if config and config.output_tokens is not None:
            output_tokens = config.output_tokens
        else:
            output_tokens = min(self._default_output_tokens, int(len(output) / 4))

        tool_calls = config.tool_calls if config else None
        resp = ModelResponse(
            content=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            finish_reason="tool_calls" if tool_calls else "stop",
            tool_calls=tool_calls,
        )
        self._call_history.append({"request": request, "response": resp})
        return resp

    async def health_check(self, model: str) -> Dict[str, Any]:
        return {"healthy": True, "message": "Explicit Mock mode", "model": model}

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelStreamEvent]:
        response = await self.generate(request)
        if response.content:
            yield ModelStreamEvent(type="token", content=response.content)
        yield ModelStreamEvent(
            type="done",
            raw={
                "usage": {
                    "prompt_tokens": response.input_tokens,
                    "completion_tokens": response.output_tokens,
                    "total_tokens": response.total_tokens,
                }
            },
        )

    def _default_output(self, prompt: str, model_id: str, system_prompt: Optional[str]) -> str:
        preview = prompt[:100].replace("\n", " ")
        return (
            f"[Mock response for {model_id}]\n"
            f"Task: {preview}...\n"
            f"Status: completed successfully.\n"
            f"Output: Generated response with estimated {self._default_output_tokens} output tokens.\n"
            f"This is a simulated output for testing purposes."
        )

    def get_call_history(self) -> list:
        return list(self._call_history)

    def reset(self) -> None:
        self._configs.clear()
        self._call_history.clear()
