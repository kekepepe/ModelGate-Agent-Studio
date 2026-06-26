import uuid
import json
from datetime import datetime, timezone
from typing import List

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, event

from src.core.database import Base


class AgentStation(Base):
    __tablename__ = "agent_stations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False, default="idle")
    current_task_id = Column(String(36))
    default_model_id = Column(String(36), nullable=False)
    backup_model_ids = Column(Text, nullable=False, default="[]")
    allowed_tools = Column(Text, nullable=False, default="[]")
    system_prompt = Column(Text, nullable=False, default="")
    output_format = Column(String(50))
    max_steps_per_task = Column(Integer, nullable=False, default=10)
    max_tool_calls_per_task = Column(Integer, default=20)
    allow_handoff = Column(Boolean, nullable=False, default=False)
    handoff_threshold_tokens = Column(Integer)
    is_enabled = Column(Boolean, nullable=False, default=True)
    total_tasks_completed = Column(Integer, nullable=False, default=0)
    total_tasks_failed = Column(Integer, nullable=False, default=0)
    total_handoffs_initiated = Column(Integer, nullable=False, default=0)
    average_tokens_per_task = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_backup_model_ids(self) -> List[str]:
        return json.loads(self.backup_model_ids) if self.backup_model_ids else []

    def set_backup_model_ids(self, model_ids: List[str]) -> None:
        self.backup_model_ids = json.dumps(model_ids)

    def get_allowed_tools(self) -> List[str]:
        return json.loads(self.allowed_tools) if self.allowed_tools else []

    def set_allowed_tools(self, tools: List[str]) -> None:
        self.allowed_tools = json.dumps(tools)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "status": self.status,
            "current_task_id": self.current_task_id,
            "default_model_id": self.default_model_id,
            "backup_model_ids": self.get_backup_model_ids(),
            "allowed_tools": self.get_allowed_tools(),
            "system_prompt": self.system_prompt,
            "output_format": self.output_format,
            "max_steps_per_task": self.max_steps_per_task,
            "max_tool_calls_per_task": self.max_tool_calls_per_task,
            "allow_handoff": self.allow_handoff,
            "handoff_threshold_tokens": self.handoff_threshold_tokens,
            "is_enabled": self.is_enabled,
            "total_tasks_completed": self.total_tasks_completed,
            "total_tasks_failed": self.total_tasks_failed,
            "total_handoffs_initiated": self.total_handoffs_initiated,
            "average_tokens_per_task": self.average_tokens_per_task,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@event.listens_for(AgentStation, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
