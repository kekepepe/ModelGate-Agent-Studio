"""Mock model provider with swappable interface.

Provides a Protocol-based interface for model providers. MockModelProvider
simulates model API calls with configurable outputs, tokens, and latency.
Call history is recorded for test assertions.

To swap in a real provider, implement the ModelProvider Protocol and call
set_provider(your_real_provider).
"""

import random
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Protocol


@dataclass
class ModelResponse:
    text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    model_name: str
    finish_reason: str = "stop"


class ModelProvider(Protocol):
    """Protocol that real providers must satisfy."""

    def generate(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> ModelResponse: ...


@dataclass
class _ModelConfig:
    output_text: Optional[str] = None
    output_text_fn: Optional[Callable[[str, Optional[str]], str]] = None
    input_tokens: Optional[int] = None
    input_tokens_fn: Optional[Callable[[str], int]] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None


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
    ) -> None:
        self._configs[model_id] = _ModelConfig(
            output_text=output_text,
            output_text_fn=output_text_fn,
            input_tokens=input_tokens,
            input_tokens_fn=input_tokens_fn,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )

    def generate(
        self,
        prompt: str,
        model_id: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> ModelResponse:
        config = self._configs.get(model_id)

        if config and config.latency_ms is not None:
            latency_ms = config.latency_ms
        else:
            latency_ms = self._default_latency_ms + random.randint(-100, 100)

        time.sleep(latency_ms / 1000.0)

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

        resp = ModelResponse(
            text=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            model_name=model_id,
            finish_reason="stop",
        )
        self._call_history.append({"prompt": prompt, "model_id": model_id, "response": resp})
        return resp

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
