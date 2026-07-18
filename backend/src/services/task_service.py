import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import WorkerSession
from src.models.model import Model
from src.models.workspace import Artifact, Task, VerificationResult
from src.services import log_service


class TaskNotFoundError(Exception):
    pass


class TaskTransitionError(Exception):
    pass


def get_task(db: Session, task_id: str) -> Dict:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise TaskNotFoundError(f"Task '{task_id}' not found")

    data = task.to_dict()

    if task.assigned_agent_id:
        agent = db.query(AgentStation).filter(AgentStation.id == task.assigned_agent_id).first()
        if agent:
            data["agent_name"] = agent.name
            data["agent_role"] = agent.role

    if task.assigned_worker_id:
        worker = db.query(WorkerSession).filter(WorkerSession.id == task.assigned_worker_id).first()
        if worker:
            data["worker_status"] = worker.status
            model = db.query(Model).filter(Model.id == worker.model_id).first() if worker.model_id else None
            data["model_name"] = model.display_name if model else None
            data["workspace_scope"] = worker.workspace_scope

    data["artifacts"] = [
        {"id": item.id, "type": item.type, "path": item.path, "checksum": item.checksum,
         "verification_status": item.verification_status, "created_at": item.created_at.isoformat() if item.created_at else None}
        for item in db.query(Artifact).filter(Artifact.task_id == task.id).all()
    ]
    data["verification_results"] = [
        {"id": item.id, "criterion_type": item.criterion_type, "command_or_rule": item.command_or_rule,
         "status": item.status, "evidence": item.evidence, "exit_code": item.exit_code,
         "created_at": item.created_at.isoformat() if item.created_at else None}
        for item in db.query(VerificationResult).filter(VerificationResult.task_id == task.id).order_by(VerificationResult.created_at.asc()).all()
    ]

    return data


def cancel_task(db: Session, task_id: str, reason: str = "Cancelled by user") -> Dict:
    task = _task_or_raise(db, task_id)
    if task.status in {"completed", "completed_verified", "cancelled"}:
        raise TaskTransitionError(f"Task cannot be cancelled from status: {task.status}")
    task.status, task.blocked_reason = "cancelled", reason
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    log_service.create_log(db, {"goal_id": task.goal_id, "task_id": task.id, "event_type": "task_status_change", "event_status": "cancelled", "output_summary": reason})
    return get_task(db, task.id)


def retry_task(db: Session, task_id: str) -> Dict:
    task = _task_or_raise(db, task_id)
    if task.status not in {"failed", "blocked", "revision_required", "completed_unverified", "cancelled"}:
        raise TaskTransitionError(f"Task cannot be retried from status: {task.status}")
    task.status, task.blocked_reason, task.verification_status = "pending", None, None
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    log_service.create_log(db, {"goal_id": task.goal_id, "task_id": task.id, "event_type": "task_status_change", "event_status": "retrying", "output_summary": "Task returned to pending by user"})
    return get_task(db, task.id)


def skip_task(db: Session, task_id: str, reason: str = "Skipped by user") -> Dict:
    task = _task_or_raise(db, task_id)
    if task.status in {"running", "completed", "completed_verified", "completed_unverified", "skipped"}:
        raise TaskTransitionError(f"Task cannot be skipped from status: {task.status}")
    task.status, task.blocked_reason = "skipped", reason
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "event_type": "task.skipped",
        "event_status": "completed",
        "output_summary": reason,
    })
    return get_task(db, task.id)


def approve_task(db: Session, task_id: str) -> Dict:
    task = _task_or_raise(db, task_id)
    if task.status != "waiting_approval":
        raise TaskTransitionError(f"Task cannot be approved from status: {task.status}")
    task.status, task.blocked_reason = "pending", None
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "event_type": "task.approved",
        "event_status": "completed",
        "output_summary": "Human approval recorded; Task returned to the scheduler",
    })
    return get_task(db, task.id)


def split_task(db: Session, task_id: str, titles: List[str]) -> List[Dict]:
    parent = _task_or_raise(db, task_id)
    if parent.status in {"running", "completed", "completed_verified", "cancelled"}:
        raise TaskTransitionError(f"Task cannot be split from status: {parent.status}")
    clean_titles = [title.strip() for title in titles if title and title.strip()]
    if len(clean_titles) < 2:
        raise TaskTransitionError("Splitting requires at least two child task titles")
    children = []
    for index, title in enumerate(clean_titles):
        child = Task(
            id=str(uuid.uuid4()), goal_id=parent.goal_id, title=title,
            description=parent.description, status="pending", assigned_agent_id=parent.assigned_agent_id,
            priority=max(parent.priority - index, 0), task_type=parent.task_type,
            risk_level=parent.risk_level, parent_task_id=parent.id,
        )
        child.set_json("required_capabilities", parent._get_json("required_capabilities"))
        child.set_json("required_tools", parent._get_json("required_tools"))
        child.set_json("acceptance_criteria", parent._get_json("acceptance_criteria"))
        child.set_json("dependencies", parent._get_json("dependencies"))
        db.add(child)
        children.append(child)
    parent.status, parent.blocked_reason = "cancelled", "Superseded by split child tasks"
    db.commit()
    log_service.create_log(db, {"goal_id": parent.goal_id, "task_id": parent.id, "event_type": "plan.updated", "event_status": "completed", "output_summary": f"Task split into {len(children)} children", "metadata": {"child_task_ids": [child.id for child in children]}})
    return [get_task(db, child.id) for child in children]


def _task_or_raise(db: Session, task_id: str) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise TaskNotFoundError(f"Task '{task_id}' not found")
    return task
