import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, UniqueConstraint, event

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
    max_parallel_tasks = Column(Integer, nullable=False, default=3)
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
            "max_parallel_tasks": self.max_parallel_tasks,
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
    plan_version_id = Column(String(36), nullable=True, index=True)
    plan_task_id = Column(String(36), nullable=True, index=True)
    plan_source = Column(String(30), nullable=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    recovery_count = Column(Integer, nullable=False, default=0)
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
            "plan_version_id": self.plan_version_id,
            "plan_task_id": self.plan_task_id,
            "plan_source": self.plan_source,
            "lease_expires_at": self.lease_expires_at.isoformat() if self.lease_expires_at else None,
            "recovery_count": self.recovery_count,
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


class ExecutionPlan(Base):
    """One immutable, validated version of a Goal's execution plan."""

    __tablename__ = "execution_plans"
    __table_args__ = (
        UniqueConstraint("goal_id", "version", name="uq_execution_plan_goal_version"),
        UniqueConstraint("plan_id", "version", name="uq_execution_plan_id_version"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), nullable=False, index=True)
    goal_id = Column(String(36), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="validated", index=True)
    task_mode = Column(String(40), nullable=False)
    goal_summary = Column(Text, nullable=False)
    assumptions = Column(Text, nullable=False, default="[]")
    required_context = Column(Text, nullable=False, default="[]")
    activation_reason = Column(Text, nullable=False)
    final_acceptance_criteria = Column(Text, nullable=False, default="[]")
    human_approval_points = Column(Text, nullable=False, default="[]")
    estimated_cost = Column(Text, nullable=False, default="{}")
    fallback_reason = Column(Text, nullable=True)
    planner_type = Column(String(30), nullable=False, default="rule_fallback")
    raw_output = Column(Text, nullable=True)
    repair_records = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    confirmed_at = Column(DateTime, nullable=True)

    def _get_json(self, field: str, default):
        import json
        value = getattr(self, field, None)
        try:
            return json.loads(value) if value else default
        except (json.JSONDecodeError, TypeError):
            return default

    def set_json(self, field: str, value) -> None:
        import json
        setattr(self, field, json.dumps(value, ensure_ascii=False))

    def to_dict(self, tasks=None) -> dict:
        payload = {
            "id": self.id,
            "plan_id": self.plan_id,
            "goal_id": self.goal_id,
            "version": self.version,
            "status": self.status,
            "task_mode": self.task_mode,
            "goal_summary": self.goal_summary,
            "assumptions": self._get_json("assumptions", []),
            "required_context": self._get_json("required_context", []),
            "activation_reason": self.activation_reason,
            "final_acceptance_criteria": self._get_json("final_acceptance_criteria", []),
            "human_approval_points": self._get_json("human_approval_points", []),
            "estimated_cost": self._get_json("estimated_cost", {}),
            "fallback_reason": self.fallback_reason,
            "planner_type": self.planner_type,
            "raw_output": self.raw_output,
            "repair_records": self._get_json("repair_records", []),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
        }
        if tasks is not None:
            payload["tasks"] = [task.to_dict() for task in tasks]
        return payload


class PlanTask(Base):
    """A plan-level task whose client ID remains stable inside one plan version."""

    __tablename__ = "plan_tasks"
    __table_args__ = (
        UniqueConstraint("plan_version_id", "client_task_id", name="uq_plan_task_client_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_version_id = Column(String(36), nullable=False, index=True)
    client_task_id = Column(String(100), nullable=False)
    objective = Column(Text, nullable=False)
    task_type = Column(String(30), nullable=False)
    required_capabilities = Column(Text, nullable=False, default="[]")
    required_tools = Column(Text, nullable=False, default="[]")
    dependencies = Column(Text, nullable=False, default="[]")
    acceptance_criteria = Column(Text, nullable=False, default="[]")
    risk_level = Column(String(20), nullable=False, default="low")
    parallel_safe = Column(Boolean, nullable=False, default=False)
    context_query = Column(Text, nullable=False, default="")
    approval_required = Column(Boolean, nullable=False, default=False)
    workspace_scope = Column(Text, nullable=True)
    merge_strategy = Column(Text, nullable=True)
    runtime_task_id = Column(String(36), nullable=True, index=True)
    source = Column(String(30), nullable=False, default="created")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def _get_json(self, field: str):
        import json
        try:
            return json.loads(getattr(self, field, None) or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def set_json(self, field: str, value) -> None:
        import json
        setattr(self, field, json.dumps(value, ensure_ascii=False))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plan_version_id": self.plan_version_id,
            "client_task_id": self.client_task_id,
            "objective": self.objective,
            "task_type": self.task_type,
            "required_capabilities": self._get_json("required_capabilities"),
            "required_tools": self._get_json("required_tools"),
            "dependencies": self._get_json("dependencies"),
            "acceptance_criteria": self._get_json("acceptance_criteria"),
            "risk_level": self.risk_level,
            "parallel_safe": self.parallel_safe,
            "context_query": self.context_query,
            "approval_required": self.approval_required,
            "workspace_scope": self.workspace_scope,
            "merge_strategy": self.merge_strategy,
            "runtime_task_id": self.runtime_task_id,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PlanChange(Base):
    """Auditable diff metadata connecting two immutable plan versions."""

    __tablename__ = "plan_changes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=False, index=True)
    from_plan_version_id = Column(String(36), nullable=True, index=True)
    to_plan_version_id = Column(String(36), nullable=False, index=True)
    change_type = Column(String(30), nullable=False, default="created")
    reason = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False, default="[]")
    retained_task_ids = Column(Text, nullable=False, default="[]")
    cancelled_task_ids = Column(Text, nullable=False, default="[]")
    added_task_ids = Column(Text, nullable=False, default="[]")
    replaced_task_ids = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def _get_json(self, field: str):
        import json
        try:
            return json.loads(getattr(self, field, None) or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def set_json(self, field: str, value) -> None:
        import json
        setattr(self, field, json.dumps(value, ensure_ascii=False))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "from_plan_version_id": self.from_plan_version_id,
            "to_plan_version_id": self.to_plan_version_id,
            "change_type": self.change_type,
            "reason": self.reason,
            "evidence": self._get_json("evidence"),
            "retained_task_ids": self._get_json("retained_task_ids"),
            "cancelled_task_ids": self._get_json("cancelled_task_ids"),
            "added_task_ids": self._get_json("added_task_ids"),
            "replaced_task_ids": self._get_json("replaced_task_ids"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


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
    base_commit_sha = Column(String(64), nullable=True)
    branch_name = Column(String(255), nullable=True, unique=True)
    agent_id = Column(String(36), nullable=True, index=True)
    commit_sha = Column(String(64), nullable=True)
    merge_commit_sha = Column(String(64), nullable=True)
    merge_output = Column(Text, nullable=True)
    conflict_files = Column(Text, nullable=False, default="[]")
    status = Column(String(30), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    merged_at = Column(DateTime, nullable=True)
    removed_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        try:
            conflicts = json.loads(self.conflict_files or "[]")
        except json.JSONDecodeError:
            conflicts = []
        return {
            "id": self.id, "goal_id": self.goal_id, "task_id": self.task_id,
            "agent_id": self.agent_id, "path": self.path, "base_ref": self.base_ref,
            "base_commit_sha": self.base_commit_sha, "branch_name": self.branch_name,
            "commit_sha": self.commit_sha, "merge_commit_sha": self.merge_commit_sha,
            "merge_output": self.merge_output, "conflict_files": conflicts,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "merged_at": self.merged_at.isoformat() if self.merged_at else None,
            "removed_at": self.removed_at.isoformat() if self.removed_at else None,
        }


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
