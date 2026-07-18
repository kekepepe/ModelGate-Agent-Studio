import json

import httpx
import pytest

from src.services.providers.base import ModelRequest, ProviderError
from src.services.providers.openai_compatible_provider import OpenAICompatibleProvider


def _request() -> ModelRequest:
    return ModelRequest(
        provider="openai",
        model="database-uuid",
        messages=[{"role": "user", "content": "hello"}],
        metadata={"provider_model_name": "real-provider-model"},
    )


def _provider(handler) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        base_url="https://provider.test/v1",
        api_key="super-secret",
        timeout=1,
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_generate_uses_provider_model_name_and_preserves_usage():
    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["model"] == "real-provider-model"
        return httpx.Response(
            200,
            headers={"x-request-id": "req-1"},
            json={
                "id": "chat-1",
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
            },
        )

    response = await _provider(handler).generate(_request())
    assert response.content == "ok"
    assert response.total_tokens == 6
    assert response.request_id == "req-1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "message", "code", "retryable"),
    [
        (401, "bad key", "provider_auth_error", False),
        (429, "slow down", "provider_rate_limited", True),
        (500, "down", "provider_unavailable", True),
        (400, "maximum context length exceeded", "provider_context_overflow", False),
    ],
)
async def test_http_failures_use_stable_taxonomy(status, message, code, retryable):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": {"message": message}})

    with pytest.raises(ProviderError) as caught:
        await _provider(handler).generate(_request())
    assert caught.value.code == code
    assert caught.value.retryable is retryable
    assert "super-secret" not in str(caught.value)


@pytest.mark.asyncio
async def test_invalid_json_and_malformed_tool_calls_are_classified():
    responses = iter([
        httpx.Response(200, text="not-json"),
        httpx.Response(200, json={"choices": [{"message": {"tool_calls": [{"id": "x"}]}}]}),
    ])

    def handler(_request: httpx.Request) -> httpx.Response:
        return next(responses)

    provider = _provider(handler)
    with pytest.raises(ProviderError, match="provider_invalid_response"):
        await provider.generate(_request())
    with pytest.raises(ProviderError, match="provider_tool_call_error"):
        await provider.generate(_request())


@pytest.mark.asyncio
async def test_timeout_and_empty_response_are_classified():
    def timeout_handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow provider")

    with pytest.raises(ProviderError, match="provider_timeout"):
        await _provider(timeout_handler).generate(_request())

    def empty_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {}, "finish_reason": "stop"}]})

    with pytest.raises(ProviderError, match="provider_empty_response"):
        await _provider(empty_handler).generate(_request())


@pytest.mark.asyncio
async def test_stream_interruption_empty_stream_and_malformed_json_are_classified():
    payloads = iter([
        'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n',
        "data: [DONE]\n\n",
        "data: not-json\n\n",
    ])

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=next(payloads))

    provider = _provider(handler)
    with pytest.raises(ProviderError, match="provider_stream_interrupted"):
        _ = [event async for event in provider.stream(_request())]
    with pytest.raises(ProviderError, match="provider_empty_response"):
        _ = [event async for event in provider.stream(_request())]
    with pytest.raises(ProviderError, match="provider_invalid_response"):
        _ = [event async for event in provider.stream(_request())]


@pytest.mark.asyncio
async def test_stream_preserves_incremental_tool_calls_and_usage():
    payload = "\n".join([
        'data: {"id":"chat-stream","choices":[{"delta":{"tool_calls":[{"index":0,"id":"call-1","type":"function","function":{"name":"file_","arguments":"{\\\"pa"}}]},"finish_reason":null}]}',
        'data: {"id":"chat-stream","choices":[{"delta":{"tool_calls":[{"index":0,"function":{"name":"read","arguments":"th\\\":\\\"README.md\\\"}"}}]},"finish_reason":"tool_calls"}]}',
        'data: {"id":"chat-stream","choices":[],"usage":{"prompt_tokens":7,"completion_tokens":3,"total_tokens":10}}',
        "data: [DONE]",
        "",
    ])

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["stream"] is True
        assert body["tools"][0]["function"]["name"] == "file_read"
        return httpx.Response(200, text=payload)

    request = _request()
    request.tools = [{"type": "function", "function": {"name": "file_read", "parameters": {}}}]
    events = [event async for event in _provider(handler).stream(request)]
    deltas = [event for event in events if event.type == "tool_call_delta"]
    assert len(deltas) == 2
    assert events[-1].raw == {
        "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
        "finish_reason": "tool_calls",
    }
    assert events[-1].request_id == "chat-stream"


def test_missing_key_is_an_auth_error():
    with pytest.raises(ProviderError) as caught:
        OpenAICompatibleProvider(base_url="https://provider.test/v1", api_key="")
    assert caught.value.code == "provider_auth_error"


def test_provider_timeout_can_be_configured_from_environment(monkeypatch):
    monkeypatch.setenv("PROVIDER_TIMEOUT_SECONDS", "37")
    provider = OpenAICompatibleProvider(base_url="https://provider.test/v1", api_key="key")
    assert provider.timeout == 37
