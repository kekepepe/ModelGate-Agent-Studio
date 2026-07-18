"""Recover expired Runtime work without replaying verified side effects."""

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.models.handoff import WorkerSession
from src.models.tool import ToolCallRecord
from src.models.workspace import Goal, Task
from src.services import log_service


NON_IDEMPOTENT_TOOL_NAMES = {"terminal_execute"}


def recover_interrupted_tasks(
    db: Session,
    goal_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, int]:
    moment = now or datetime.now(timezone.utc)
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return {"recovered": 0, "approval_required": 0}

    recovered = 0
    approval_required = 0
    running = db.query(Task).filter(Task.goal_id == goal_id, Task.status == "running").all()
    for task in running:
        lease = task.lease_expires_at
        if lease is not None:
            comparable = lease if lease.tzinfo else lease.replace(tzinfo=timezone.utc)
            if comparable > moment:
                continue
        unsafe_effect = db.query(ToolCallRecord).filter(
            ToolCallRecord.task_id == task.id,
            ToolCallRecord.status == "completed",
            ToolCallRecord.tool_name.in_(NON_IDEMPOTENT_TOOL_NAMES),
            ToolCallRecord.idempotency_key.is_(None),
        ).first()
        if unsafe_effect:
            task.status = "waiting_approval"
            task.blocked_reason = (
                f"Recovery paused after non-idempotent tool '{unsafe_effect.tool_name}'. "
                "Confirm before replaying the Task."
            )
            approval_required += 1
        else:
            task.status = "pending"
            task.blocked_reason = "Recovered after an expired worker lease."
            recovered += 1
        task.lease_expires_at = None
        task.recovery_count = (task.recovery_count or 0) + 1
        if task.assigned_worker_id:
            worker = db.query(WorkerSession).filter(WorkerSession.id == task.assigned_worker_id).first()
            if worker and worker.status == "running":
                worker.status = "recoverable"
                worker.next_action = "approval" if unsafe_effect else "retry"
        log_service.create_log(db, {
            "goal_id": goal_id,
            "task_id": task.id,
            "event_type": "task.recovered",
            "event_status": task.status,
            "output_summary": task.blocked_reason,
            "metadata": {"recovery_count": task.recovery_count, "lease_expired_at": str(lease)},
        }, commit=False)
    if recovered or approval_required:
        db.commit()
    return {"recovered": recovered, "approval_required": approval_required}
