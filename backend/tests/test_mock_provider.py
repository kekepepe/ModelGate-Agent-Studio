import pytest
from src.services.mock_provider import MockModelProvider, ModelResponse


class TestMockModelProvider:
    def test_generate_returns_valid_response(self):
        provider = MockModelProvider()
        resp = provider.generate("test prompt", "test-model")
        assert isinstance(resp, ModelResponse)
        assert resp.text
        assert resp.total_tokens == resp.input_tokens + resp.output_tokens
        assert resp.latency_ms >= 0
        assert resp.finish_reason == "stop"

    def test_configured_output_text(self):
        provider = MockModelProvider()
        provider.configure_model("test-model", output_text="Custom output text")
        resp = provider.generate("p", "test-model")
        assert resp.text == "Custom output text"

    def test_configured_output_text_fn(self):
        provider = MockModelProvider()
        provider.configure_model(
            "m",
            output_text_fn=lambda prompt, sys: f"Got: {prompt} (sys: {sys})",
        )
        resp = provider.generate("hello", "m", system_prompt="be helpful")
        assert "hello" in resp.text
        assert "be helpful" in resp.text

    def test_configured_tokens(self):
        provider = MockModelProvider()
        provider.configure_model("m", input_tokens=100, output_tokens=50)
        resp = provider.generate("p", "m")
        assert resp.input_tokens == 100
        assert resp.output_tokens == 50
        assert resp.total_tokens == 150

    def test_configured_latency(self):
        provider = MockModelProvider()
        provider.configure_model("m", latency_ms=1)
        resp = provider.generate("p", "m")
        assert resp.latency_ms == 1

    def test_configured_input_tokens_fn(self):
        provider = MockModelProvider()
        provider.configure_model("m", input_tokens_fn=lambda prompt: len(prompt) * 10)
        resp = provider.generate("hi", "m")
        assert resp.input_tokens == 20

    def test_call_history(self):
        provider = MockModelProvider()
        provider.generate("p1", "m1")
        provider.generate("p2", "m2")
        assert len(provider.get_call_history()) == 2
        assert provider.get_call_history()[0]["model_id"] == "m1"
        assert provider.get_call_history()[1]["prompt"] == "p2"

    def test_reset_clears_config_and_history(self):
        provider = MockModelProvider()
        provider.configure_model("m", output_text="custom")
        provider.generate("p", "m")
        provider.reset()
        assert len(provider.get_call_history()) == 0
        resp = provider.generate("p", "m")
        assert resp.text != "custom"

    def test_default_output_includes_model_id(self):
        provider = MockModelProvider()
        resp = provider.generate("prompt text", "my-awesome-model")
        assert "my-awesome-model" in resp.text
        assert "prompt text" in resp.text
