"""Base interfaces for model providers.

Defines the ModelProvider protocol and request/response data classes.
All providers (mock or real) must implement this interface.
"""

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol


class ProviderError(RuntimeError):
    """Stable provider failure contract consumed by Runtime recovery policy."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.retryable = retryable
        self.status_code = status_code
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "status_code": self.status_code,
            "request_id": self.request_id,
        }


@dataclass
class ModelRequest:
    provider: str
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    raw_response: Optional[Dict[str, Any]] = None
    finish_reason: str = "stop"
    tool_calls: Optional[List[Dict[str, Any]]] = None
    request_id: Optional[str] = None


@dataclass
class ModelStreamEvent:
    type: str
    content: str = ""
    request_id: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class ModelProvider(Protocol):
    """Protocol that all model providers must satisfy."""

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model."""
        ...

    async def health_check(self, model: str) -> Dict[str, Any]:
        ...

    def stream(self, request: ModelRequest) -> AsyncIterator[ModelStreamEvent]:
        ...
