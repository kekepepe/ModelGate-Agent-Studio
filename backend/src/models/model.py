import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, event

from src.core.database import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    capability_tags = Column(Text, nullable=False, default="[]")
    max_context_tokens = Column(Integer, nullable=False, default=131072)
    cost_level = Column(Integer, nullable=False, default=3)
    speed_level = Column(Integer, nullable=False, default=3)
    is_enabled = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    api_key = Column(Text, nullable=True, default=None)
    api_base_url = Column(String(500), nullable=True, default=None)
    # V1.3: USD per 1M tokens. Nullable — an unpriced model keeps FinalSummary
    # cost.available=False instead of inventing numbers.
    price_input = Column(Float, nullable=True, default=None)
    price_output = Column(Float, nullable=True, default=None)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_capability_tags(self) -> List[str]:
        return json.loads(self.capability_tags) if self.capability_tags else []

    def set_capability_tags(self, tags: List[str]) -> None:
        self.capability_tags = json.dumps(tags)

    def compute_cost(self, input_tokens: int, output_tokens: int) -> Optional[float]:
        """USD cost for a call, or None when either price is unconfigured.

        Prices are USD per 1M tokens; None means 'honest unknown', never 0.
        """
        if self.price_input is None or self.price_output is None:
            return None
        return round(
            (input_tokens / 1_000_000) * self.price_input
            + (output_tokens / 1_000_000) * self.price_output,
            6,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider": self.provider,
            "model_name": self.model_name,
            "display_name": self.display_name,
            "capability_tags": self.get_capability_tags(),
            "max_context_tokens": self.max_context_tokens,
            "cost_level": self.cost_level,
            "speed_level": self.speed_level,
            "is_enabled": self.is_enabled,
            "is_default": self.is_default,
            "has_api_key": bool(self.api_key),
            "api_base_url": self.api_base_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@event.listens_for(Model, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
