import httpx

from src.services.embedding_service import (
    LocalHashEmbeddingAdapter,
    RealEmbeddingProviderAdapter,
    ResilientEmbeddingAdapter,
    embedding_metadata,
)


def test_real_embedding_adapter_records_model_and_dimensions():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/embeddings"
        assert request.headers["authorization"] == "Bearer key"
        return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2, 0.3]}]})

    adapter = RealEmbeddingProviderAdapter(
        base_url="https://provider.test/v1",
        api_key="key",
        model_name="embed-v1",
        transport=httpx.MockTransport(handler),
    )
    vector = adapter.embed("hello")
    metadata = embedding_metadata(adapter, vector)
    assert vector == [0.1, 0.2, 0.3]
    assert metadata["embedding_dimensions"] == 3
    assert metadata["embedding_model"] == "embed-v1"


def test_real_embedding_failure_visibly_falls_back_to_local_hash():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": {"message": "unavailable"}})

    adapter = ResilientEmbeddingAdapter(
        RealEmbeddingProviderAdapter(
            base_url="https://provider.test/v1",
            api_key="key",
            model_name="embed-v1",
            transport=httpx.MockTransport(handler),
        ),
        LocalHashEmbeddingAdapter(),
    )
    vector = adapter.embed("hello")
    assert len(vector) == 64
    assert adapter.name == "local_hash"
    assert adapter.fallback_reason
