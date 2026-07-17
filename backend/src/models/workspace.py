import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, event

from src.core.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    team_preset = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="idle", index=True)
    execution_mode = Column(String(20), nullable=False, default="live")
    workspace_root = Column(Text, nullable=True)
    run_id = Column(String(36), nullable=True, index=True)
    final_verification_status = Column(String(50), nullable=True)
    budget_tokens = Column(Integer, nullable=False, default=100000)
    budget_cost_usd = Column(Float, nullable=True)
    max_duration_seconds = Column(Integer, nullable=False, default=3600)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "team_preset": self.team_preset,
            "status": self.status,
            "execution_mode": self.execution_mode,
            "workspace_root": self.workspace_root,
            "run_id": self.run_id,
            "final_verification_status": self.final_verification_status,
            "budget_tokens": self.budget_tokens,
            "budget_cost_usd": self.budget_cost_usd,
            "max_duration_seconds": self.max_duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    assigned_agent_id = Column(String(36), nullable=True, index=True)
    assigned_worker_id = Column(String(36), nullable=True)
    output = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Integer, nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    task_type = Column(String(50), nullable=False, default="general")
    required_capabilities = Column(Text, nullable=False, default="[]")
    required_tools = Column(Text, nullable=False, default="[]")
    dependencies = Column(Text, nullable=False, default="[]")
    acceptance_criteria = Column(Text, nullable=False, default="[]")
    risk_level = Column(String(20), nullable=False, default="low")
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=2)
    verification_status = Column(String(50), nullable=True)
    blocked_reason = Column(Text, nullable=True)
    parent_task_id = Column(String(36), nullable=True, index=True)
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
            "assigned_worker_id": self.assigned_worker_id,
            "output": self.output,
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
            "priority": self.priority,
            "task_type": self.task_type,
            "required_capabilities": self._get_json("required_capabilities"),
            "required_tools": self._get_json("required_tools"),
            "dependencies": self._get_json("dependencies"),
            "acceptance_criteria": self._get_json("acceptance_criteria"),
            "risk_level": self.risk_level,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "verification_status": self.verification_status,
            "blocked_reason": self.blocked_reason,
            "parent_task_id": self.parent_task_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def _get_json(self, field: str):
        import json
        value = getattr(self, field, "[]")
        try:
            return json.loads(value or "[]")
        except json.JSONDecodeError:
            return []

    def set_json(self, field: str, value) -> None:
        import json
        setattr(self, field, json.dumps(value))


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), nullable=True, index=True)
    task_id = Column(String(36), nullable=False, index=True)
    type = Column(String(50), nullable=False, default="file")
    path = Column(Text, nullable=True)
    checksum = Column(String(128), nullable=True)
    verification_status = Column(String(50), nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), nullable=False, index=True)
    criterion_type = Column(String(50), nullable=False)
    command_or_rule = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    evidence = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class WorkspaceCheckpoint(Base):
    __tablename__ = "workspace_checkpoints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=False, index=True)
    task_id = Column(String(36), nullable=False, index=True)
    path = Column(Text, nullable=False)
    existed = Column(Boolean, nullable=False, default=False)
    content = Column(Text, nullable=True)
    checksum = Column(String(128), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class WorkspaceWorktree(Base):
    __tablename__ = "workspace_worktrees"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=False, index=True)
    task_id = Column(String(36), nullable=False, unique=True, index=True)
    path = Column(Text, nullable=False, unique=True)
    base_ref = Column(String(255), nullable=False, default="HEAD")
    status = Column(String(30), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    removed_at = Column(DateTime, nullable=True)


class RuntimeRun(Base):
    __tablename__ = "runtime_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=False, index=True)
    execution_mode = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False, default="running")
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)
    final_verification_status = Column(String(50), nullable=True)
    budget_tokens = Column(Integer, nullable=False, default=100000)
    budget_cost_usd = Column(Float, nullable=True)
    max_duration_seconds = Column(Integer, nullable=False, default=3600)


@event.listens_for(Goal, "before_update")
@event.listens_for(Task, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
