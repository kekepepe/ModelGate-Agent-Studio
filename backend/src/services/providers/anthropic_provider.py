"""Anthropic native provider (V1.3 P2) — messages API via httpx.

Mirrors the proven OpenAICompatibleProvider shape: an OpenAI-style
ModelRequest goes in, the Anthropic Messages API is called, and the
response is translated back into the OpenAI-style ModelResponse contract
(tool_calls included) so the runtime tool loop needs zero changes.

Protocol notes (api.anthropic.com):
  - auth headers: x-api-key + anthropic-version
  - system prompt is a top-level field, not a message role
  - tools: [{name, description, input_schema}] (JSON Schema)
  - tool_use blocks come back in content; tool results are sent back as
    user messages with content blocks of type tool_result
  - stop_reason: end_turn | max_tokens | stop_sequence | tool_use
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import httpx

from src.services.providers.base import ModelRequest, ModelResponse, ProviderError


class AnthropicProviderError(ProviderError):
    """Normalized provider error contract for the Anthropic native adapter."""


ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider:
    """Native adapter for the Anthropic Messages API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.base_url: str = (
            base_url
            or os.environ.get("ANTHROPIC_BASE_URL")
            or "https://api.anthropic.com"
        )
        self.api_key: str = api_key or os.environ.get("ANTHROPIC_API_KEY") or ""
        timeout_value = os.environ.get("PROVIDER_TIMEOUT_SECONDS") or "60"
        self.timeout = timeout if timeout is not None else int(timeout_value)
        self.transport = transport

        if not self.api_key:
            raise AnthropicProviderError(
                "provider_auth_error",
                "An Anthropic API key is required for live execution.",
                retryable=False,
            )

    # ------------------------------------------------------------------ #
    # Request translation: OpenAI-style -> Anthropic Messages API
    # ------------------------------------------------------------------ #

    def _split_system(self, messages: List[Dict[str, Any]]) -> tuple:
        system_parts: List[str] = []
        rest: List[Dict[str, Any]] = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if role == "system":
                if content:
                    system_parts.append(str(content))
                continue
            rest.append(message)
        return ("\n".join(system_parts) or None), rest

    def _translate_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None
        translated = []
        for tool in tools:
            function = tool.get("function", {}) if tool.get("type") == "function" else tool
            translated.append({
                "name": function.get("name"),
                "description": function.get("description", ""),
                "input_schema": function.get("parameters") or {"type": "object", "properties": {}},
            })
        return [item for item in translated if item["name"]]

    def _translate_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        translated: List[Dict[str, Any]] = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if role == "assistant" and message.get("tool_calls"):
                blocks: List[Dict[str, Any]] = []
                if content:
                    blocks.append({"type": "text", "text": str(content)})
                for call in message["tool_calls"]:
                    function = call.get("function", {})
                    try:
                        arguments = json.loads(function.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        arguments = {}
                    blocks.append({
                        "type": "tool_use",
                        "id": call.get("id") or f"call_{len(blocks)}",
                        "name": function.get("name"),
                        "input": arguments,
                    })
                translated.append({"role": "assistant", "content": blocks})
            elif role == "tool":
                translated.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": message.get("tool_call_id") or "",
                        "content": str(content or ""),
                    }],
                })
            else:
                # plain user / assistant text
                translated.append({"role": role or "user", "content": str(content or "")})
        return translated

    # ------------------------------------------------------------------ #
    # generate
    # ------------------------------------------------------------------ #

    async def generate(self, request: ModelRequest) -> ModelResponse:
        start_time = time.time()
        system, rest = self._split_system(request.messages)

        payload: Dict[str, Any] = {
            "model": request.metadata.get("provider_model_name", request.model),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": self._translate_messages(rest),
        }
        if system:
            payload["system"] = system
        tools = self._translate_tools(request.tools)
        if tools:
            payload["tools"] = tools

        url = f"{self.base_url.rstrip('/')}/v1/messages"
        headers = self._headers()

        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                resp = await client.post(url, json=payload, headers=headers)

            if resp.status_code != 200:
                raise self._http_error(resp)

            try:
                data = resp.json()
                content_blocks = data["content"]
                usage = data["usage"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise AnthropicProviderError(
                    "provider_invalid_response",
                    "Anthropic returned an invalid messages payload.",
                    retryable=True,
                    status_code=resp.status_code,
                    request_id=resp.headers.get("request-id"),
                ) from exc

            text_parts = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
            content = "".join(text_parts)
            tool_calls = self._tool_use_to_openai(content_blocks)

            stop_reason = data.get("stop_reason", "end_turn")
            finish_reason = "tool_calls" if stop_reason == "tool_use" else "stop"

            if not content and not tool_calls:
                raise AnthropicProviderError(
                    "provider_empty_response",
                    "Anthropic returned neither text nor tool_use blocks.",
                    retryable=True,
                    status_code=resp.status_code,
                    request_id=data.get("id"),
                )

            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            return ModelResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                latency_ms=int((time.time() - start_time) * 1000),
                raw_response=data,
                finish_reason=finish_reason,
                tool_calls=tool_calls,
                request_id=data.get("id"),
            )

        except httpx.TimeoutException as exc:
            raise AnthropicProviderError(
                "provider_timeout",
                f"Anthropic request timed out after {self.timeout}s.",
                retryable=True,
            ) from exc
        except httpx.ConnectError as exc:
            raise AnthropicProviderError(
                "provider_unavailable",
                "Cannot connect to the Anthropic endpoint.",
                retryable=True,
            ) from exc

    # ------------------------------------------------------------------ #
    # health check (GET /v1/models is free and validates auth + reachability)
    # ------------------------------------------------------------------ #

    async def health_check(self, model: str) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/v1/models?limit=1"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                response = await client.get(url, headers=self._headers())
            if response.status_code == 200:
                return {"healthy": True, "latency_ms": 0, "request_id": response.headers.get("request-id")}
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
                "message": "Anthropic health endpoint is unavailable.",
                "retryable": True,
            }

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _tool_use_to_openai(content_blocks: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        tool_calls = [
            {
                "id": block.get("id") or "",
                "type": "function",
                "function": {
                    "name": block.get("name") or "",
                    "arguments": json.dumps(block.get("input") or {}),
                },
            }
            for block in content_blocks
            if block.get("type") == "tool_use"
        ]
        return tool_calls or None

    def _http_error(self, response: httpx.Response) -> AnthropicProviderError:
        status = response.status_code
        request_id = response.headers.get("request-id")
        detail = self._safe_error_detail(response)
        if status in {401, 403}:
            return AnthropicProviderError("provider_auth_error", detail or "Anthropic authentication failed.", retryable=False, status_code=status, request_id=request_id)
        if status == 429:
            return AnthropicProviderError("provider_rate_limited", detail or "Anthropic rate limit reached.", retryable=True, status_code=status, request_id=request_id)
        if status in {408, 504}:
            return AnthropicProviderError("provider_timeout", detail or "Anthropic request timed out.", retryable=True, status_code=status, request_id=request_id)
        if status == 529 or (status >= 500):
            return AnthropicProviderError("provider_unavailable", detail or "Anthropic is temporarily unavailable (possibly overloaded).", retryable=True, status_code=status, request_id=request_id)
        return AnthropicProviderError("provider_invalid_response", detail or "Anthropic rejected the request.", retryable=False, status_code=status, request_id=request_id)

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
        return re.sub(r"(?i)x-api-key\s*[:=]\s*[a-z0-9._-]+", "x-api-key: [REDACTED]", detail)
