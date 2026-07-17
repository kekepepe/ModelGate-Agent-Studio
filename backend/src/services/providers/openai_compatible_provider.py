"""OpenAI-compatible model provider for real API calls.

Supports any OpenAI-compatible endpoint (OpenAI, Anthropic via proxy,
local models via Ollama/vLLM, etc.).

Configuration via environment variables:
  OPENAI_BASE_URL  - API base URL (default: https://api.openai.com/v1)
  OPENAI_API_KEY   - API key (required)
  OPENAI_TIMEOUT   - Request timeout in seconds (default: 60)
"""

import os
import time
import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from src.services.providers.base import ModelRequest, ModelResponse, ModelStreamEvent


class OpenAICompatibleError(Exception):
    pass


class OpenAICompatibleProvider:
    """Provider for OpenAI-compatible API endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 60,
    ):
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout

        if not self.api_key:
            raise OpenAICompatibleError(
                "OPENAI_API_KEY is required. Set it via environment variable or pass api_key parameter."
            )

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Send a chat completion request to the OpenAI-compatible endpoint."""
        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": request.metadata.get("provider_model_name", request.model),
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.tools:
            payload["tools"] = request.tools

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)

            if resp.status_code == 429:
                raise OpenAICompatibleError("Rate limited (429). Consider retry or switching model.")
            elif resp.status_code >= 500:
                raise OpenAICompatibleError(f"Provider error ({resp.status_code}): {resp.text[:200]}")
            elif resp.status_code != 200:
                raise OpenAICompatibleError(f"API error ({resp.status_code}): {resp.text[:200]}")

            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})

            latency_ms = int((time.time() - start_time) * 1000)

            message = choice.get("message", {})
            tool_calls = message.get("tool_calls") or None
            return ModelResponse(
                content=message.get("content") or "",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                latency_ms=latency_ms,
                raw_response=data,
                finish_reason=choice.get("finish_reason", "stop"),
                tool_calls=tool_calls,
                request_id=resp.headers.get("x-request-id") or data.get("id"),
            )

        except httpx.TimeoutException:
            raise OpenAICompatibleError(f"Request timed out after {self.timeout}s")

        except httpx.ConnectError:
            raise OpenAICompatibleError(f"Cannot connect to {url}. Check OPENAI_BASE_URL.")

        except httpx.HTTPStatusError as e:
            raise OpenAICompatibleError(f"HTTP error: {e.response.status_code}")

    async def health_check(self, model: str) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/models/{model}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers={"Authorization": f"Bearer {self.api_key}"})
            if response.status_code == 200:
                return {"healthy": True, "latency_ms": 0, "request_id": response.headers.get("x-request-id")}
            return {"healthy": False, "status_code": response.status_code, "message": response.text[:200]}
        except httpx.TimeoutException:
            return {"healthy": False, "message": f"Health check timed out after {self.timeout}s"}
        except httpx.HTTPError as exc:
            return {"healthy": False, "message": str(exc)}

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelStreamEvent]:
        payload: Dict[str, Any] = {"model": request.metadata.get("provider_model_name", request.model), "messages": request.messages, "stream": True}
        if request.tools:
            payload["tools"] = request.tools
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        raise OpenAICompatibleError(f"Streaming API error ({response.status_code}): {(await response.aread()).decode()[:200]}")
                    request_id = response.headers.get("x-request-id")
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            yield ModelStreamEvent(type="done", request_id=request_id)
                            return
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content") or ""
                            if content:
                                yield ModelStreamEvent(type="token", content=content, request_id=request_id, raw=chunk)
                        except json.JSONDecodeError:
                            continue
        except httpx.TimeoutException as exc:
            raise OpenAICompatibleError(f"Stream timed out after {self.timeout}s") from exc

    def _build_messages(self, system_prompt: Optional[str], prompt: str) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages
