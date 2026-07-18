import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, event

from src.core.database import Base


class ToolDefinition(Base):
    __tablename__ = "tool_definitions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False, default="")
    category = Column(String(50), nullable=False, default="其他")
    risk_level = Column(String(10), nullable=False, default="low")
    parameters = Column(Text, nullable=False, default="{}")
    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_parameters(self) -> Dict[str, Any]:
        return json.loads(self.parameters) if self.parameters else {}

    def set_parameters(self, params: Dict[str, Any]) -> None:
        self.parameters = json.dumps(params)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "risk_level": self.risk_level,
            "parameters": self.get_parameters(),
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@event.listens_for(ToolDefinition, "before_update")
def receive_tool_before_update(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)


class ToolCallRecord(Base):
    __tablename__ = "tool_call_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=True)
    task_id = Column(String(36), nullable=True)
    agent_id = Column(String(36), nullable=True)
    worker_id = Column(String(36), nullable=True)
    tool_name = Column(String(100), nullable=False)
    tool_input = Column(Text, nullable=False, default="{}")
    tool_output = Column(Text, nullable=True)
    result_data = Column(Text, nullable=False, default="{}")
    idempotency_key = Column(String(64), nullable=True, unique=True, index=True)
    status = Column(String(20), nullable=False, default="started")
    latency_ms = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_tool_input(self) -> Dict[str, Any]:
        return json.loads(self.tool_input) if self.tool_input else {}

    def set_tool_input(self, data: Dict[str, Any]) -> None:
        self.tool_input = json.dumps(data)

    def get_result(self) -> Dict[str, Any]:
        try:
            return json.loads(self.result_data or "{}")
        except json.JSONDecodeError:
            return {}

    def set_result(self, data: Dict[str, Any]) -> None:
        self.result_data = json.dumps(data, ensure_ascii=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "worker_id": self.worker_id,
            "tool_name": self.tool_name,
            "tool_input": self.get_tool_input(),
            "tool_output": self.tool_output,
            "idempotency_key": self.idempotency_key,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "result": self.get_result() or {
                "tool_call_id": self.id,
                "tool_name": self.tool_name,
                "status": "success" if self.status == "completed" else self.status,
                "exit_code": 0 if self.status == "completed" else None,
                "stdout": self.tool_output or "",
                "stderr": self.error_message or "",
                "duration_ms": self.latency_ms,
                "truncated": bool(self.tool_output and self.tool_output.endswith("[output truncated]")),
            },
        }
