"""Base interfaces for model providers.

Defines the ModelProvider protocol and request/response data classes.
All providers (mock or real) must implement this interface.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


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


class ModelProvider(Protocol):
    """Protocol that all model providers must satisfy."""

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model."""
        ...
