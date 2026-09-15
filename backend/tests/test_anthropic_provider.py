"""V1.3 P2: AnthropicProvider — native messages-API adapter.

The adapter must translate OpenAI-style requests into Anthropic Messages
calls and translate responses (including tool_use blocks) back into the
OpenAI-style ModelResponse contract, so the runtime tool loop works
unchanged. All live traffic is exercised through httpx.MockTransport.
"""
import json

import httpx
import pytest

from src.services.providers.anthropic_provider import AnthropicProvider, AnthropicProviderError
from src.services.providers.base import ModelRequest
from src.services.providers.provider_factory import create_provider


def _request(**overrides) -> ModelRequest:
    base = dict(
        provider="anthropic",
        model="database-uuid",
        messages=[{"role": "user", "content": "hello"}],
        metadata={"provider_model_name": "claude-sonnet-4-6"},
    )
    base.update(overrides)
    return ModelRequest(**base)


def _provider(handler) -> AnthropicProvider:
    return AnthropicProvider(
        base_url="https://anthropic.test",
        api_key="super-secret",
        timeout=1,
        transport=httpx.MockTransport(handler),
    )


def test_create_provider_routes_anthropic_to_native_adapter():
    provider = create_provider("anthropic", api_key="k", base_url="https://anthropic.test")
    assert isinstance(provider, AnthropicProvider)


@pytest.mark.asyncio
async def test_generate_translates_request_and_response():
    seen = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        body = json.loads(request.content)
        seen["body"] = body
        return httpx.Response(200, json={
            "id": "msg_1",
            "content": [{"type": "text", "text": "hi there"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 7, "output_tokens": 3},
        })

    response = await _provider(handler).generate(_request())

    assert seen["url"] == "https://anthropic.test/v1/messages"
    assert seen["headers"]["x-api-key"] == "super-secret"
    assert seen["headers"]["anthropic-version"] == "2023-06-01"
    assert seen["body"]["model"] == "claude-sonnet-4-6"
    assert seen["body"]["max_tokens"] == 4096
    assert response.content == "hi there"
    assert response.input_tokens == 7
    assert response.output_tokens == 3
    assert response.total_tokens == 10
    assert response.finish_reason == "stop"


@pytest.mark.asyncio
async def test_generate_translates_system_and_tools():
    async def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={
            "id": "msg_2",
            "content": [{"type": "text", "text": "reading"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 5, "output_tokens": 2},
        })

    seen = {}
    request = _request(
        messages=[
            {"role": "system", "content": "be brief"},
            {"role": "user", "content": "read the file"},
        ],
        tools=[{
            "type": "function",
            "function": {
                "name": "file_read",
                "description": "read a file",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
            },
        }],
    )
    await _provider(handler).generate(request)

    assert seen["body"]["system"] == "be brief"
    assert seen["body"]["tools"] == [{
        "name": "file_read",
        "description": "read a file",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
    }]
    assert all(m["role"] != "system" for m in seen["body"]["messages"])


@pytest.mark.asyncio
async def test_tool_use_blocks_map_back_to_openai_tool_calls():
    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        # The runtime's previous assistant tool_calls must arrive as
        # Anthropic tool_use blocks, and tool results as tool_result blocks.
        assert body["messages"][1]["content"][0]["type"] == "tool_use"
        assert body["messages"][1]["content"][0]["input"] == {"path": "a.py"}
        assert body["messages"][2]["content"][0]["type"] == "tool_result"
        assert body["messages"][2]["content"][0]["tool_use_id"] == "call1"
        return httpx.Response(200, json={
            "id": "msg_3",
            "content": [{"type": "tool_use", "id": "tu_9", "name": "file_write", "input": {"path": "b.py"}}],
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 9, "output_tokens": 4},
        })

    request = _request(messages=[
        {"role": "user", "content": "list files"},
        {"role": "assistant", "content": "", "tool_calls": [{
            "id": "call1", "type": "function",
            "function": {"name": "file_read", "arguments": json.dumps({"path": "a.py"})},
        }]},
        {"role": "tool", "tool_call_id": "call1", "content": "file content"},
    ])

    response = await _provider(handler).generate(request)

    assert response.finish_reason == "tool_calls"
    assert response.tool_calls == [{
        "id": "tu_9", "type": "function",
        "function": {"name": "file_write", "arguments": json.dumps({"path": "b.py"})},
    }]


@pytest.mark.asyncio
async def test_error_classification():
    cases = [
        (401, "provider_auth_error", False),
        (429, "provider_rate_limited", True),
        (500, "provider_unavailable", True),
        (529, "provider_unavailable", True),  # anthropic overloaded
    ]
    for status, expected_code, expected_retryable in cases:
        async def handler(request: httpx.Request, status=status) -> httpx.Response:
            return httpx.Response(status, json={"error": {"type": "error", "message": "boom"}})

        with pytest.raises(AnthropicProviderError) as exc_info:
            await _provider(handler).generate(_request())
        assert exc_info.value.code == expected_code
        assert exc_info.value.retryable is expected_retryable
        assert "super-secret" not in str(exc_info.value), "api key must be redacted"


@pytest.mark.asyncio
async def test_health_check_uses_models_endpoint():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).endswith("/v1/models?limit=1")
        return httpx.Response(200, json={"data": []})

    result = await _provider(handler).health_check("claude-sonnet-4-6")
    assert result["healthy"] is True


@pytest.mark.asyncio
async def test_health_check_failure_reports_unhealthy():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    result = await _provider(handler).health_check("claude-sonnet-4-6")
    assert result["healthy"] is False


def test_missing_key_fails_loudly(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(AnthropicProviderError):
        AnthropicProvider(base_url="https://anthropic.test", api_key="")
