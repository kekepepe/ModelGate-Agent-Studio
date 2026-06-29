import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Integer, Float, DateTime

from src.core.database import Base


class QuotaRecord(Base):
    __tablename__ = "quota_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(50), nullable=False)
    model_id = Column(String(36), nullable=False)
    model_name = Column(String(100), nullable=False)
    request_count = Column(Integer, nullable=False, default=0)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    limit_error_count = Column(Integer, nullable=False, default=0)
    handoff_triggered_count = Column(Integer, nullable=False, default=0)
    quota_mode = Column(String(20), nullable=False, default="unknown")
    token_limit = Column(Integer, nullable=True)
    request_limit = Column(Integer, nullable=True)
    cost_limit = Column(Float, nullable=True)
    reset_period = Column(String(20), nullable=True)
    reset_date = Column(Integer, nullable=True)
    usage_percent = Column(Float, nullable=True)
    estimated_remaining = Column(Integer, nullable=True)
    quota_status = Column(String(20), nullable=False, default="unknown")
    last_used_at = Column(DateTime, nullable=True)
    cooldown_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider": self.provider,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "request_count": self.request_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "limit_error_count": self.limit_error_count,
            "handoff_triggered_count": self.handoff_triggered_count,
            "quota_mode": self.quota_mode,
            "token_limit": self.token_limit,
            "request_limit": self.request_limit,
            "cost_limit": self.cost_limit,
            "reset_period": self.reset_period,
            "reset_date": self.reset_date,
            "usage_percent": self.usage_percent,
            "estimated_remaining": self.estimated_remaining,
            "quota_status": self.quota_status,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "cooldown_until": self.cooldown_until.isoformat() if self.cooldown_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
