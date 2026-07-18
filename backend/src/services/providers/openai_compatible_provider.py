"""OpenAI-compatible model provider for real API calls.

Supports any OpenAI-compatible endpoint (OpenAI, Anthropic via proxy,
local models via Ollama/vLLM, etc.).

Configuration via environment variables:
  OPENAI_BASE_URL  - API base URL (default: https://api.openai.com/v1)
  OPENAI_API_KEY   - API key (required)
  OPENAI_TIMEOUT   - Request timeout in seconds (default: 60)
"""

import json
import os
import re
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from src.services.providers.base import ModelRequest, ModelResponse, ModelStreamEvent, ProviderError


class OpenAICompatibleError(ProviderError):
    """Backward-compatible name for the normalized provider error contract."""


class OpenAICompatibleProvider:
    """Provider for OpenAI-compatible API endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.base_url: str = base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.api_key: str = api_key or os.environ.get("OPENAI_API_KEY") or ""
        timeout_value = (
            os.environ.get("PROVIDER_TIMEOUT_SECONDS")
            or os.environ.get("OPENAI_TIMEOUT")
            or "60"
        )
        self.timeout = timeout if timeout is not None else int(timeout_value)
        self.transport = transport

        if not self.api_key:
            raise OpenAICompatibleError(
                "provider_auth_error",
                "An API key is required for live execution.",
                retryable=False,
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
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                resp = await client.post(url, json=payload, headers=headers)

            if resp.status_code != 200:
                raise self._http_error(resp)

            try:
                data = resp.json()
                choice = data["choices"][0]
                message = choice.get("message", {})
            except (json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError) as exc:
                raise OpenAICompatibleError(
                    "provider_invalid_response",
                    "Provider returned an invalid chat completion payload.",
                    retryable=True,
                    status_code=resp.status_code,
                    request_id=resp.headers.get("x-request-id"),
                ) from exc
            usage = data.get("usage", {})

            latency_ms = int((time.time() - start_time) * 1000)

            tool_calls = message.get("tool_calls") or None
            if tool_calls is not None and not self._valid_tool_calls(tool_calls):
                raise OpenAICompatibleError(
                    "provider_tool_call_error",
                    "Provider returned malformed tool calls.",
                    retryable=True,
                    status_code=resp.status_code,
                    request_id=resp.headers.get("x-request-id") or data.get("id"),
                )
            content = message.get("content") or ""
            if not content and not tool_calls:
                raise OpenAICompatibleError(
                    "provider_empty_response",
                    "Provider returned neither content nor tool calls.",
                    retryable=True,
                    status_code=resp.status_code,
                    request_id=resp.headers.get("x-request-id") or data.get("id"),
                )
            return ModelResponse(
                content=content,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                latency_ms=latency_ms,
                raw_response=data,
                finish_reason=choice.get("finish_reason", "stop"),
                tool_calls=tool_calls,
                request_id=resp.headers.get("x-request-id") or data.get("id"),
            )

        except httpx.TimeoutException as exc:
            raise OpenAICompatibleError(
                "provider_timeout",
                f"Provider request timed out after {self.timeout}s.",
                retryable=True,
            ) from exc

        except httpx.ConnectError as exc:
            raise OpenAICompatibleError(
                "provider_unavailable",
                "Cannot connect to the configured provider endpoint.",
                retryable=True,
            ) from exc

        except httpx.HTTPStatusError as e:
            raise self._http_error(e.response) from e

    async def health_check(self, model: str) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/models/{model}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                response = await client.get(url, headers={"Authorization": f"Bearer {self.api_key}"})
            if response.status_code == 200:
                return {"healthy": True, "latency_ms": 0, "request_id": response.headers.get("x-request-id")}
            error = self._http_error(response)
            return {"healthy": False, **error.to_dict()}
        except httpx.TimeoutException:
            return {
                "healthy": False,
                "code": "provider_timeout",
                "message": f"Health check timed out after {self.timeout}s.",
                "retryable": True,
            }
        except httpx.HTTPError:
            return {
                "healthy": False,
                "code": "provider_unavailable",
                "message": "Provider health endpoint is unavailable.",
                "retryable": True,
            }

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelStreamEvent]:
        payload: Dict[str, Any] = {
            "model": request.metadata.get("provider_model_name", request.model),
            "messages": request.messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.tools:
            payload["tools"] = request.tools
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        await response.aread()
                        raise self._http_error(response)
                    request_id = response.headers.get("x-request-id")
                    last_usage: Dict[str, Any] = {}
                    finish_reason = "stop"
                    emitted_activity = False
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            if not emitted_activity and not last_usage:
                                raise OpenAICompatibleError(
                                    "provider_empty_response",
                                    "Provider stream ended without content.",
                                    retryable=True,
                                    request_id=request_id,
                                )
                            yield ModelStreamEvent(
                                type="done",
                                request_id=request_id,
                                raw={"usage": last_usage, "finish_reason": finish_reason},
                            )
                            return
                        try:
                            chunk = json.loads(data)
                            request_id = request_id or chunk.get("id")
                            if chunk.get("usage"):
                                last_usage = chunk["usage"]
                            choices = chunk.get("choices") or []
                            choice = choices[0] if choices else {}
                            finish_reason = choice.get("finish_reason") or finish_reason
                            delta = choice.get("delta", {})
                            content = delta.get("content") or ""
                            if content:
                                emitted_activity = True
                                yield ModelStreamEvent(type="token", content=content, request_id=request_id, raw=chunk)
                            tool_call_deltas = delta.get("tool_calls") or []
                            if tool_call_deltas:
                                if not isinstance(tool_call_deltas, list) or not all(
                                    isinstance(item, dict) and isinstance(item.get("index"), int)
                                    for item in tool_call_deltas
                                ):
                                    raise OpenAICompatibleError(
                                        "provider_tool_call_error",
                                        "Provider returned malformed streaming tool calls.",
                                        retryable=True,
                                        request_id=request_id,
                                    )
                                emitted_activity = True
                                yield ModelStreamEvent(
                                    type="tool_call_delta", request_id=request_id, raw=chunk,
                                )
                        except json.JSONDecodeError as exc:
                            raise OpenAICompatibleError(
                                "provider_invalid_response",
                                "Provider returned malformed streaming JSON.",
                                retryable=True,
                                request_id=request_id,
                            ) from exc
                    raise OpenAICompatibleError(
                        "provider_stream_interrupted",
                        "Provider stream closed before the completion marker.",
                        retryable=True,
                        request_id=request_id,
                    )
        except httpx.TimeoutException as exc:
            raise OpenAICompatibleError(
                "provider_timeout",
                f"Provider stream timed out after {self.timeout}s.",
                retryable=True,
            ) from exc
        except httpx.ConnectError as exc:
            raise OpenAICompatibleError(
                "provider_unavailable",
                "Provider stream connection failed.",
                retryable=True,
            ) from exc

    def _http_error(self, response: httpx.Response) -> OpenAICompatibleError:
        status = response.status_code
        request_id = response.headers.get("x-request-id")
        detail = self._safe_error_detail(response)
        if status in {401, 403}:
            return OpenAICompatibleError("provider_auth_error", detail or "Provider authentication failed.", retryable=False, status_code=status, request_id=request_id)
        if status == 429:
            return OpenAICompatibleError("provider_rate_limited", detail or "Provider rate limit reached.", retryable=True, status_code=status, request_id=request_id)
        if status in {408, 504}:
            return OpenAICompatibleError("provider_timeout", detail or "Provider request timed out.", retryable=True, status_code=status, request_id=request_id)
        if status == 400 and "context" in detail.lower() and any(word in detail.lower() for word in ("length", "window", "token", "overflow")):
            return OpenAICompatibleError("provider_context_overflow", detail, retryable=False, status_code=status, request_id=request_id)
        if status >= 500:
            return OpenAICompatibleError("provider_unavailable", detail or "Provider is temporarily unavailable.", retryable=True, status_code=status, request_id=request_id)
        return OpenAICompatibleError("provider_invalid_response", detail or "Provider rejected the request.", retryable=False, status_code=status, request_id=request_id)

    def _safe_error_detail(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            detail = error.get("message", "") if isinstance(error, dict) else ""
        except (json.JSONDecodeError, TypeError, AttributeError):
            detail = ""
        if not detail:
            detail = response.reason_phrase or ""
        detail = detail[:200]
        if self.api_key:
            detail = detail.replace(self.api_key, "[REDACTED]")
        return re.sub(r"(?i)bearer\s+[a-z0-9._-]+", "Bearer [REDACTED]", detail)

    @staticmethod
    def _valid_tool_calls(tool_calls: Any) -> bool:
        if not isinstance(tool_calls, list):
            return False
        return all(
            isinstance(call, dict)
            and isinstance(call.get("id"), str)
            and isinstance(call.get("function"), dict)
            and isinstance(call["function"].get("name"), str)
            and isinstance(call["function"].get("arguments"), str)
            for call in tool_calls
        )

    def _build_messages(self, system_prompt: Optional[str], prompt: str) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages
