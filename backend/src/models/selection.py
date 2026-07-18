import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Text

from src.core.database import Base


class AgentSelectionDecision(Base):
    """Immutable evidence for one joint Agent and model selection."""

    __tablename__ = "agent_selection_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=True, index=True)
    task_id = Column(String(100), nullable=False, index=True)
    required_capabilities = Column(Text, nullable=False, default="[]")
    required_tools = Column(Text, nullable=False, default="[]")
    candidates = Column(Text, nullable=False, default="[]")
    selected_agent_id = Column(String(36), nullable=False, index=True)
    selected_model_id = Column(String(36), nullable=False, index=True)
    backup_model_ids = Column(Text, nullable=False, default="[]")
    score = Column(Float, nullable=False)
    selection_reason = Column(Text, nullable=False)
    fallback_entry = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "required_capabilities": json.loads(self.required_capabilities or "[]"),
            "required_tools": json.loads(self.required_tools or "[]"),
            "candidates": json.loads(self.candidates or "[]"),
            "selected_agent_id": self.selected_agent_id,
            "selected_model_id": self.selected_model_id,
            "backup_model_ids": json.loads(self.backup_model_ids or "[]"),
            "score": self.score,
            "selection_reason": self.selection_reason,
            "fallback_entry": json.loads(self.fallback_entry or "{}"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
