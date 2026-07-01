from typing import Optional
import pytest
from src.services.providers.base import ModelRequest, ModelResponse
from src.services.providers.mock_provider import MockModelProvider


def _make_request(prompt: str, model_id: str = "test-model", system_prompt: Optional[str] = None) -> ModelRequest:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return ModelRequest(provider="test", model=model_id, messages=messages)


class TestMockModelProvider:
    @pytest.mark.asyncio
    async def test_generate_returns_valid_response(self):
        provider = MockModelProvider()
        resp = await provider.generate(_make_request("test prompt"))
        assert isinstance(resp, ModelResponse)
        assert resp.content
        assert resp.total_tokens == resp.input_tokens + resp.output_tokens
        assert resp.latency_ms >= 0
        assert resp.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_configured_output_text(self):
        provider = MockModelProvider()
        provider.configure_model("test-model", output_text="Custom output text")
        resp = await provider.generate(_make_request("p", "test-model"))
        assert resp.content == "Custom output text"

    @pytest.mark.asyncio
    async def test_configured_output_text_fn(self):
        provider = MockModelProvider()
        provider.configure_model("m", output_text_fn=lambda prompt, sys: f"Got: {prompt} (sys: {sys})")
        resp = await provider.generate(_make_request("hello", "m", system_prompt="be helpful"))
        assert "hello" in resp.content
        assert "be helpful" in resp.content

    @pytest.mark.asyncio
    async def test_configured_tokens(self):
        provider = MockModelProvider()
        provider.configure_model("m", input_tokens=100, output_tokens=50)
        resp = await provider.generate(_make_request("p", "m"))
        assert resp.input_tokens == 100
        assert resp.output_tokens == 50
        assert resp.total_tokens == 150

    @pytest.mark.asyncio
    async def test_configured_latency(self):
        provider = MockModelProvider()
        provider.configure_model("m", latency_ms=1)
        resp = await provider.generate(_make_request("p", "m"))
        assert resp.latency_ms == 1

    @pytest.mark.asyncio
    async def test_configured_input_tokens_fn(self):
        provider = MockModelProvider()
        provider.configure_model("m", input_tokens_fn=lambda prompt: len(prompt) * 10)
        resp = await provider.generate(_make_request("hi", "m"))
        assert resp.input_tokens == 20

    @pytest.mark.asyncio
    async def test_call_history(self):
        provider = MockModelProvider()
        await provider.generate(_make_request("p1", "m1"))
        await provider.generate(_make_request("p2", "m2"))
        assert len(provider.get_call_history()) == 2
        assert provider.get_call_history()[0]["request"].model == "m1"

    @pytest.mark.asyncio
    async def test_reset_clears_config_and_history(self):
        provider = MockModelProvider()
        provider.configure_model("m", output_text="custom")
        await provider.generate(_make_request("p", "m"))
        provider.reset()
        assert len(provider.get_call_history()) == 0
        resp = await provider.generate(_make_request("p", "m"))
        assert resp.content != "custom"

    @pytest.mark.asyncio
    async def test_default_output_includes_model_id(self):
        provider = MockModelProvider()
        resp = await provider.generate(_make_request("prompt text", "my-awesome-model"))
        assert "my-awesome-model" in resp.content
        assert "prompt text" in resp.content
