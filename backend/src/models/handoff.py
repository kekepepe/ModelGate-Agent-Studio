import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, event

from src.core.database import Base


class HandoffRecord(Base):
    __tablename__ = "handoff_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=False)
    task_id = Column(String(36), nullable=False, index=True)
    from_agent_id = Column(String(36), nullable=False)
    from_model_id = Column(String(100), nullable=False)
    from_worker_id = Column(String(36), nullable=True)
    to_agent_id = Column(String(36), nullable=False)
    to_model_id = Column(String(100), nullable=False)
    to_worker_id = Column(String(36), nullable=True)
    reason = Column(String(50), nullable=False)
    reason_description = Column(Text, nullable=True)
    handoff_summary = Column(Text, nullable=False, default="{}")
    status = Column(String(50), nullable=False, default="requested", index=True)
    result_after_handoff = Column(String(20), nullable=True)
    result_note = Column(Text, nullable=True)
    tokens_before_handoff = Column(Integer, nullable=False, default=0)
    tokens_after_handoff = Column(Integer, nullable=False, default=0)
    time_saved_estimate_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    summary_generated_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_handoff_summary(self) -> Dict[str, Any]:
        return json.loads(self.handoff_summary) if self.handoff_summary else {}

    def set_handoff_summary(self, summary: Dict[str, Any]) -> None:
        self.handoff_summary = json.dumps(summary, ensure_ascii=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "from_agent_id": self.from_agent_id,
            "from_model_id": self.from_model_id,
            "from_worker_id": self.from_worker_id,
            "to_agent_id": self.to_agent_id,
            "to_model_id": self.to_model_id,
            "to_worker_id": self.to_worker_id,
            "reason": self.reason,
            "reason_description": self.reason_description,
            "handoff_summary": self.get_handoff_summary(),
            "status": self.status,
            "result_after_handoff": self.result_after_handoff,
            "result_note": self.result_note,
            "tokens_before_handoff": self.tokens_before_handoff,
            "tokens_after_handoff": self.tokens_after_handoff,
            "time_saved_estimate_ms": self.time_saved_estimate_ms,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "summary_generated_at": self.summary_generated_at.isoformat() if self.summary_generated_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class HandoffTask(Base):
    __tablename__ = "handoff_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    status = Column(String(50), nullable=False, default="running", index=True)
    assigned_agent_id = Column(String(36), nullable=False)
    assigned_model_id = Column(String(100), nullable=False)
    assigned_worker_id = Column(String(36), nullable=True)
    current_output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "assigned_agent_id": self.assigned_agent_id,
            "assigned_model_id": self.assigned_model_id,
            "assigned_worker_id": self.assigned_worker_id,
            "current_output": self.current_output,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkerSession(Base):
    __tablename__ = "worker_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), nullable=False)
    model_id = Column(String(100), nullable=False)
    goal_id = Column(String(36), nullable=False)
    task_id = Column(String(36), nullable=False)
    inherited_from_handoff_id = Column(String(36), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="running")
    current_context = Column(Text, nullable=True)
    final_output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    total_tokens_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "model_id": self.model_id,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "inherited_from_handoff_id": self.inherited_from_handoff_id,
            "status": self.status,
            "current_context": self.current_context,
            "final_output": self.final_output,
            "error_message": self.error_message,
            "total_tokens_used": self.total_tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=True, index=True)
    task_id = Column(String(36), nullable=True, index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    worker_id = Column(String(36), nullable=True)
    model_id = Column(String(100), nullable=True, index=True)
    handoff_id = Column(String(36), nullable=True, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    event_status = Column(String(50), nullable=False, index=True)

    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    token_usage = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)

    error_type = Column(String(50), nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    tool_name = Column(String(100), nullable=True)
    quota_status = Column(String(50), nullable=True)
    handoff_status = Column(String(50), nullable=True)

    extra_metadata = Column(Text, nullable=True)
    routing_info = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_token_usage(self) -> Dict[str, Any]:
        return json.loads(self.token_usage) if self.token_usage else {}

    def set_token_usage(self, value: Dict[str, Any]) -> None:
        self.token_usage = json.dumps(value, ensure_ascii=False)

    def get_metadata(self) -> Dict[str, Any]:
        return json.loads(self.extra_metadata) if self.extra_metadata else {}

    def set_metadata(self, value: Dict[str, Any]) -> None:
        self.extra_metadata = json.dumps(value, ensure_ascii=False)

    def get_routing_info(self) -> Dict[str, Any]:
        return json.loads(self.routing_info) if self.routing_info else {}

    def set_routing_info(self, value: Dict[str, Any]) -> None:
        self.routing_info = json.dumps(value, ensure_ascii=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "worker_id": self.worker_id,
            "model_id": self.model_id,
            "handoff_id": self.handoff_id,
            "event_type": self.event_type,
            "event_status": self.event_status,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "token_usage": self.get_token_usage(),
            "latency_ms": self.latency_ms,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "tool_name": self.tool_name,
            "quota_status": self.quota_status,
            "handoff_status": self.handoff_status,
            "metadata": self.get_metadata(),
            "routing_info": self.get_routing_info(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@event.listens_for(HandoffRecord, "before_update")
@event.listens_for(HandoffTask, "before_update")
@event.listens_for(WorkerSession, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
