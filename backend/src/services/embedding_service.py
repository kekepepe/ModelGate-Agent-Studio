"""Versioned embedding adapters with visible local fallback behavior."""

import os
from typing import Callable, List, Optional, Protocol

import httpx

from src.services.knowledge_source_service import _hash_embedding
from src.services.providers.provider_config import provider_api_base, provider_api_key


class EmbeddingError(RuntimeError):
    pass


class EmbeddingAdapter(Protocol):
    name: str
    model_name: str
    version: str
    fallback_reason: Optional[str]

    def embed(self, text: str) -> List[float]: ...

    @property
    def fingerprint(self) -> str: ...


class LocalHashEmbeddingAdapter:
    name = "local_hash"
    model_name = "sha256-token-hash"
    version = "1"
    fallback_reason: Optional[str] = None

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    @property
    def fingerprint(self) -> str:
        return f"{self.name}:{self.model_name}:{self.version}:{self.dimensions}"

    def embed(self, text: str) -> List[float]:
        return _hash_embedding(text, self.dimensions)


class RealEmbeddingProviderAdapter:
    name = "openai_compatible"
    version = "1"
    fallback_reason: Optional[str] = None

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 30,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.base_url = base_url or provider_api_base() or "https://api.openai.com/v1"
        self.api_key = api_key or provider_api_key()
        self.model_name = model_name or os.environ.get("EMBEDDING_MODEL_NAME") or ""
        self.timeout = timeout
        self.transport = transport
        self.dimensions: Optional[int] = None
        if not self.api_key or not self.model_name:
            raise EmbeddingError("Real embeddings require PROVIDER_API_KEY and EMBEDDING_MODEL_NAME")

    @property
    def fingerprint(self) -> str:
        # Provider vector dimensions are discovered at runtime.  Keep the
        # ingestion-version fingerprint stable across process restarts and
        # record the actual dimensions separately in chunk metadata.
        return f"{self.name}:{self.model_name}:{self.version}"

    def embed(self, text: str) -> List[float]:
        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                response = client.post(
                    f"{self.base_url.rstrip('/')}/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model_name, "input": text},
                )
            response.raise_for_status()
            vector = response.json()["data"][0]["embedding"]
            if not isinstance(vector, list) or not vector:
                raise ValueError("empty embedding")
            result = [float(value) for value in vector]
            self.dimensions = len(result)
            return result
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise EmbeddingError("Embedding provider returned no usable vector") from exc


class OptionalLocalEmbeddingModelAdapter:
    name = "optional_local_model"
    version = "1"
    fallback_reason: Optional[str] = None

    def __init__(self, model_name: str, embed_fn: Callable[[str], List[float]]) -> None:
        self.model_name = model_name
        self._embed_fn = embed_fn
        self.dimensions: Optional[int] = None

    @property
    def fingerprint(self) -> str:
        return f"{self.name}:{self.model_name}:{self.version}"

    def embed(self, text: str) -> List[float]:
        vector = [float(value) for value in self._embed_fn(text)]
        if not vector:
            raise EmbeddingError("Local embedding model returned an empty vector")
        self.dimensions = len(vector)
        return vector


class ResilientEmbeddingAdapter:
    """Use a configured real adapter, then visibly pin to local fallback."""

    def __init__(self, primary: EmbeddingAdapter, fallback: EmbeddingAdapter) -> None:
        self.primary = primary
        self.fallback = fallback
        self.active = primary
        self.fallback_reason: Optional[str] = None

    @property
    def name(self) -> str:
        return self.active.name

    @property
    def model_name(self) -> str:
        return self.active.model_name

    @property
    def version(self) -> str:
        return self.active.version

    @property
    def fingerprint(self) -> str:
        return self.active.fingerprint

    def embed(self, text: str) -> List[float]:
        try:
            return self.active.embed(text)
        except EmbeddingError as exc:
            if self.active is self.fallback:
                raise
            self.active = self.fallback
            self.fallback_reason = str(exc)
            return self.active.embed(text)


def configured_embedding_adapter() -> EmbeddingAdapter:
    backend = os.environ.get("EMBEDDING_BACKEND", "local_hash").lower()
    fallback = LocalHashEmbeddingAdapter()
    if backend == "local_hash":
        return fallback
    if backend == "real":
        try:
            return ResilientEmbeddingAdapter(RealEmbeddingProviderAdapter(), fallback)
        except EmbeddingError as exc:
            fallback.fallback_reason = str(exc)
            return fallback
    raise EmbeddingError(f"Unsupported EMBEDDING_BACKEND: {backend}")


def embedding_metadata(adapter: EmbeddingAdapter, vector: List[float]) -> dict:
    return {
        "embedding_adapter": adapter.name,
        "embedding_model": adapter.model_name,
        "embedding_version": adapter.version,
        "embedding_dimensions": len(vector),
        "embedding_fingerprint": adapter.fingerprint,
        "embedding_fallback_reason": adapter.fallback_reason,
    }
