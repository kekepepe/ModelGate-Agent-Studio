from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, Optional, Tuple
import uuid
import hashlib
import os

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord, HandoffTask, WorkerSession
from src.models.model import Model
from src.models.workspace import Goal, RuntimeRun, Task
from src.models.workspace import Artifact, VerificationResult, WorkspaceCheckpoint
from src.models.tool import ToolCallRecord
from src.schemas.handoff import HandoffTaskCreate
from src.services.security_service import redact_data, redact_text

HANDOFF_STATUS_REQUESTED = "requested"
HANDOFF_STATUS_GENERATING = "generating_summary"
HANDOFF_STATUS_READY = "ready"
HANDOFF_STATUS_ACCEPTED = "accepted"
HANDOFF_STATUS_COMPLETED = "completed"
HANDOFF_STATUS_FAILED = "failed"

ACTIVE_HANDOFF_STATUSES = {
    HANDOFF_STATUS_REQUESTED,
    HANDOFF_STATUS_GENERATING,
    HANDOFF_STATUS_READY,
    HANDOFF_STATUS_ACCEPTED,
}

VALID_TRANSITIONS = {
    HANDOFF_STATUS_REQUESTED: {HANDOFF_STATUS_GENERATING, HANDOFF_STATUS_FAILED},
    HANDOFF_STATUS_GENERATING: {HANDOFF_STATUS_READY, HANDOFF_STATUS_FAILED},
    HANDOFF_STATUS_READY: {HANDOFF_STATUS_ACCEPTED, HANDOFF_STATUS_FAILED},
    HANDOFF_STATUS_ACCEPTED: {HANDOFF_STATUS_COMPLETED, HANDOFF_STATUS_FAILED},
    HANDOFF_STATUS_COMPLETED: set(),
    HANDOFF_STATUS_FAILED: set(),
}

REQUIRED_SUMMARY_FIELDS = [
    "original_goal",
    "current_task",
    "completed_work",
    "unfinished_work",
    "important_constraints",
    "key_decisions",
    "errors_and_risks",
    "next_suggested_steps",
    "context_needed",
    "changed_files",
    "tool_results",
    "verification_state",
    "workspace_checkpoint",
    "recommended_next_action",
]

STATUS_EVENT_MAP = {
    HANDOFF_STATUS_REQUESTED: ("handoff_created", "created"),
    HANDOFF_STATUS_GENERATING: ("agent_step", "running"),
    HANDOFF_STATUS_READY: ("agent_step", "completed"),
    HANDOFF_STATUS_ACCEPTED: ("handoff_completed", "accepted"),
    HANDOFF_STATUS_COMPLETED: ("handoff_completed", "completed"),
    HANDOFF_STATUS_FAILED: ("error", "failed"),
}


class HandoffServiceError(Exception):
    pass


class HandoffNotFoundError(HandoffServiceError):
    pass


class HandoffValidationError(HandoffServiceError):
    pass


class HandoffConflictError(HandoffServiceError):
    pass


def is_active_handoff(status: str) -> bool:
    return status in ACTIVE_HANDOFF_STATUSES


def validate_transition(current_status: str, next_status: str) -> None:
    if next_status not in VALID_TRANSITIONS.get(current_status, set()):
        raise HandoffValidationError(f"Invalid handoff status transition: {current_status} -> {next_status}")


def _set_status(db: Session, handoff: HandoffRecord, next_status: str, message: Optional[str] = None) -> None:
    validate_transition(handoff.status, next_status)
    handoff.status = next_status
    now = datetime.now(timezone.utc)
    handoff.updated_at = now

    if next_status == HANDOFF_STATUS_READY:
        handoff.summary_generated_at = now
    elif next_status == HANDOFF_STATUS_ACCEPTED:
        handoff.accepted_at = now
    elif next_status in {HANDOFF_STATUS_COMPLETED, HANDOFF_STATUS_FAILED}:
        handoff.completed_at = now

    event_type, event_status = STATUS_EVENT_MAP[next_status]
    _create_log(
        db,
        handoff=handoff,
        event_type=event_type,
        event_status=event_status,
        output_summary=message or f"Handoff status changed to {next_status}",
    )


def _validate_summary(summary: Dict) -> Dict:
    summary = redact_data(summary)
    normalized = {}
    for field in REQUIRED_SUMMARY_FIELDS:
        value = summary.get(field)
        if field in {"original_goal", "current_task", "workspace_checkpoint", "recommended_next_action"}:
            normalized[field] = value if isinstance(value, str) and value else "—"
        else:
            normalized[field] = value if isinstance(value, list) else []
    return normalized


def _build_fallback_summary(
    db: Session,
    task: Any,
    from_agent: AgentStation,
    to_agent: AgentStation,
    reason: str,
    reason_description: Optional[str] = None,
) -> Dict:
    current_output = getattr(task, "current_output", None) or getattr(task, "output", None)
    error_message = getattr(task, "error_message", None)
    goal = task.goal_id
    goal_record = None
    # Workspace tasks carry a real Goal record; legacy HandoffTask records do not.
    # The caller may attach it to avoid changing the legacy task schema.
    if hasattr(task, "_workspace_goal"):
        goal_record = task._workspace_goal

    completed_work = []
    if current_output:
        completed_work.append(current_output)
    else:
        completed_work.append("已保留当前任务上下文，等待接手 Agent 继续推进。")

    risks = []
    if error_message:
        risks.append(error_message)
    if reason_description:
        risks.append(reason_description)
    if not risks:
        risks.append("当前未记录明确错误，交接原因来自用户或系统判断。")

    artifacts = db.query(Artifact).filter(Artifact.task_id == task.id).all() if isinstance(task, Task) else []
    tool_calls = db.query(ToolCallRecord).filter(ToolCallRecord.task_id == task.id).order_by(ToolCallRecord.created_at.desc()).limit(10).all() if isinstance(task, Task) else []
    verifications = db.query(VerificationResult).filter(VerificationResult.task_id == task.id).all() if isinstance(task, Task) else []
    checkpoint = db.query(WorkspaceCheckpoint).filter(WorkspaceCheckpoint.task_id == task.id).order_by(WorkspaceCheckpoint.created_at.desc()).first() if isinstance(task, Task) else None
    return _validate_summary({
        "original_goal": goal_record.title if goal_record else f"Goal {goal}",
        "current_task": task.description or task.title,
        "completed_work": completed_work,
        "unfinished_work": [f"由 {to_agent.name} 继续完成：{task.title}"],
        "important_constraints": ["保持原始 Goal 和当前 Task 的上下文连续性。"],
        "key_decisions": [f"任务从 {from_agent.name} 交接给 {to_agent.name}。"],
        "errors_and_risks": risks,
        "next_suggested_steps": [
            "先阅读 handoff_summary 中的已完成工作和风险。",
            "确认当前任务目标后继续执行。",
        ],
        "context_needed": ["原始 Goal", "当前 Task 描述", "交接原因", "最近输出或错误信息"],
        "changed_files": [{"path": item.path, "checksum": item.checksum} for item in artifacts],
        "tool_results": [{"tool": item.tool_name, "status": item.status, "output": (item.tool_output or "")[:500]} for item in tool_calls],
        "verification_state": [{"criterion": item.criterion_type, "status": item.status, "evidence": item.evidence} for item in verifications],
        "workspace_checkpoint": checkpoint.id if checkpoint else "",
        "recommended_next_action": "Inspect the current workspace, then continue the unfinished verification.",
    })


def _create_log(
    db: Session,
    handoff: HandoffRecord,
    event_type: str,
    event_status: str,
    output_summary: str,
    agent_id: Optional[str] = None,
    worker_id: Optional[str] = None,
    model_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ExecutionLog:
    log = ExecutionLog(
        goal_id=handoff.goal_id,
        task_id=handoff.task_id,
        agent_id=agent_id or handoff.from_agent_id,
        worker_id=worker_id or handoff.from_worker_id,
        model_id=model_id or handoff.from_model_id,
        handoff_id=handoff.id,
        event_type=event_type,
        event_status=event_status,
        output_summary=redact_text(output_summary),
    )
    if metadata:
        log.set_metadata(redact_data(metadata))
    db.add(log)
    return log


def _get_task(db: Session, task_id: str) -> Any:
    """Resolve a normal Workspace Task first, then retain legacy demo-task support."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        goal = db.query(Goal).filter(Goal.id == task.goal_id).first()
        if goal:
            task._workspace_goal = goal
        return task
    task = db.query(HandoffTask).filter(HandoffTask.id == task_id).first()
    if not task:
        raise HandoffNotFoundError(f"Task '{task_id}' not found")
    return task


def _task_model_id(db: Session, task: Any, agent: AgentStation) -> str:
    """Use the active worker model for Workspace tasks, with an Agent default fallback."""
    legacy_model_id = getattr(task, "assigned_model_id", None)
    if legacy_model_id:
        return legacy_model_id
    worker_id = getattr(task, "assigned_worker_id", None)
    if worker_id:
        worker = db.query(WorkerSession).filter(WorkerSession.id == worker_id).first()
        if worker and worker.model_id:
            return worker.model_id
    return agent.default_model_id


def _set_task_model_id(task: Any, model_id: str) -> None:
    """The legacy task persists a model id; Workspace tasks derive it from WorkerSession."""
    if isinstance(task, HandoffTask):
        task.assigned_model_id = model_id


def _get_agent(db: Session, agent_id: str) -> AgentStation:
    agent = db.query(AgentStation).filter(AgentStation.id == agent_id).first()
    if not agent:
        raise HandoffNotFoundError(f"Agent '{agent_id}' not found")
    if not agent.is_enabled:
        raise HandoffConflictError(f"Agent '{agent_id}' is disabled")
    return agent


def _get_handoff(db: Session, handoff_id: str) -> HandoffRecord:
    handoff = db.query(HandoffRecord).filter(HandoffRecord.id == handoff_id).first()
    if not handoff:
        raise HandoffNotFoundError(f"Handoff '{handoff_id}' not found")
    return handoff


def _resolve_model_id(db: Session, agent: AgentStation, model_id: Optional[str]) -> str:
    resolved = model_id or agent.default_model_id
    model = db.query(Model).filter(Model.id == resolved).first()
    if model and not model.is_enabled:
        raise HandoffConflictError(f"Model '{resolved}' is disabled")
    return resolved


def create_demo_task(db: Session, data: HandoffTaskCreate) -> HandoffTask:
    _get_agent(db, data.assigned_agent_id)
    task_id = str(uuid.uuid4())
    worker_id = str(uuid.uuid4())
    task = HandoffTask(
        id=task_id,
        goal_id=data.goal_id,
        title=data.title,
        description=data.description or "",
        status=data.status,
        assigned_agent_id=data.assigned_agent_id,
        assigned_model_id=data.assigned_model_id,
        current_output=data.current_output,
        error_message=data.error_message,
    )
    worker = WorkerSession(
        id=worker_id,
        agent_id=data.assigned_agent_id,
        model_id=data.assigned_model_id,
        goal_id=data.goal_id,
        task_id=task_id,
        status="running" if data.status == "running" else data.status,
    )
    task.assigned_worker_id = worker_id
    db.add(task)
    db.add(worker)
    db.commit()
    db.refresh(task)
    return task


def trigger_handoff(
    db: Session,
    task_id: str,
    to_agent_id: str,
    to_model_id: Optional[str],
    reason: str,
    reason_description: Optional[str] = None,
) -> Dict:
    task = _get_task(db, task_id)

    active = db.query(HandoffRecord).filter(
        HandoffRecord.task_id == task_id,
        HandoffRecord.status.in_(ACTIVE_HANDOFF_STATUSES),
    ).first()
    if active:
        raise HandoffConflictError("Task already has an active handoff")

    if task.status not in {"assigned", "running", "failed", "handoff"}:
        raise HandoffValidationError("Task status must be assigned, running, or failed to trigger handoff")

    from_agent = _get_agent(db, task.assigned_agent_id)
    to_agent = _get_agent(db, to_agent_id)
    from_model_id = _task_model_id(db, task, from_agent)
    resolved_to_model_id = _resolve_model_id(db, to_agent, to_model_id)

    handoff = HandoffRecord(
        goal_id=task.goal_id,
        task_id=task.id,
        from_agent_id=task.assigned_agent_id,
        from_model_id=from_model_id,
        from_worker_id=task.assigned_worker_id,
        to_agent_id=to_agent.id,
        to_model_id=resolved_to_model_id,
        reason=reason,
        reason_description=reason_description,
        status=HANDOFF_STATUS_REQUESTED,
        tokens_before_handoff=0,
        tokens_after_handoff=0,
    )
    handoff.set_handoff_summary(_validate_summary({}))
    db.add(handoff)
    db.flush()

    task.status = "handoff"
    from_agent.status = "handoff"
    from_agent.total_handoffs_initiated = (from_agent.total_handoffs_initiated or 0) + 1

    _create_log(
        db,
        handoff=handoff,
        event_type="handoff_created",
        event_status="created",
        output_summary=f"Handoff requested: {from_agent.name} -> {to_agent.name} ({reason})",
        metadata={"handoff_reason": reason, "trigger_type": "manual" if reason == "manual" else "auto"},
    )

    _set_status(db, handoff, HANDOFF_STATUS_GENERATING, "Generating handoff summary")
    summary = _build_fallback_summary(db, task, from_agent, to_agent, reason, reason_description)
    handoff.set_handoff_summary(summary)
    _set_status(db, handoff, HANDOFF_STATUS_READY, "Handoff summary ready")

    db.commit()
    db.refresh(handoff)

    return {
        "handoff_id": handoff.id,
        "task_id": task.id,
        "status": handoff.status,
        "message": "交接摘要已生成，等待接手 Agent 接受",
    }


def get_handoff(db: Session, handoff_id: str) -> Dict:
    handoff = _get_handoff(db, handoff_id)
    return _serialize_handoff(db, handoff)


def list_handoffs(
    db: Session,
    goal_id: Optional[str] = None,
    task_id: Optional[str] = None,
    reason: Optional[str] = None,
    status: Optional[str] = None,
    from_agent_id: Optional[str] = None,
    to_agent_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    query = db.query(HandoffRecord)
    if goal_id:
        query = query.filter(HandoffRecord.goal_id == goal_id)
    if task_id:
        query = query.filter(HandoffRecord.task_id == task_id)
    if reason:
        query = query.filter(HandoffRecord.reason == reason)
    if status:
        query = query.filter(HandoffRecord.status == status)
    if from_agent_id:
        query = query.filter(HandoffRecord.from_agent_id == from_agent_id)
    if to_agent_id:
        query = query.filter(HandoffRecord.to_agent_id == to_agent_id)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(HandoffRecord.id.ilike(like), HandoffRecord.goal_id.ilike(like), HandoffRecord.task_id.ilike(like)))

    total = query.count()
    handoffs = query.order_by(HandoffRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [_serialize_handoff_list_item(db, handoff) for handoff in handoffs]
    total_pages = ceil(total / page_size) if page_size > 0 else 0
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}


def accept_handoff(db: Session, handoff_id: str, agent_id: Optional[str] = None, model_id: Optional[str] = None) -> Dict:
    handoff = _get_handoff(db, handoff_id)
    if handoff.status != HANDOFF_STATUS_READY:
        raise HandoffValidationError("Only ready handoffs can be accepted")

    accept_agent_id = agent_id or handoff.to_agent_id
    accept_model_id = model_id or handoff.to_model_id
    agent = _get_agent(db, accept_agent_id)
    _resolve_model_id(db, agent, accept_model_id)
    task = _get_task(db, handoff.task_id)
    _validate_workspace_consistency(db, task, handoff.get_handoff_summary())

    worker = WorkerSession(
        agent_id=accept_agent_id,
        model_id=accept_model_id,
        goal_id=handoff.goal_id,
        task_id=handoff.task_id,
        inherited_from_handoff_id=handoff.id,
        status="running",
        current_context=handoff.handoff_summary,
    )
    db.add(worker)
    db.flush()

    handoff.to_agent_id = accept_agent_id
    handoff.to_model_id = accept_model_id
    handoff.to_worker_id = worker.id
    task.status = "running"
    task.assigned_agent_id = accept_agent_id
    _set_task_model_id(task, accept_model_id)
    task.assigned_worker_id = worker.id
    agent.status = "running"
    goal = db.query(Goal).filter(Goal.id == handoff.goal_id).first()
    if goal and goal.status == "handoff":
        goal.status = "running"
        if goal.run_id:
            run = db.query(RuntimeRun).filter(RuntimeRun.id == goal.run_id).first()
            if run:
                run.status = "running"

    if handoff.from_worker_id:
        previous_worker = db.query(WorkerSession).filter(WorkerSession.id == handoff.from_worker_id).first()
        if previous_worker:
            previous_worker.status = "handoff_required"

    _set_status(db, handoff, HANDOFF_STATUS_ACCEPTED, "Handoff accepted and worker session created")
    _create_log(
        db,
        handoff=handoff,
        event_type="handoff_completed",
        event_status="accepted",
        output_summary="New worker session created from handoff",
        agent_id=accept_agent_id,
        worker_id=worker.id,
        model_id=accept_model_id,
        metadata={"acceptance_time_ms": 0},
    )

    db.commit()
    db.refresh(worker)
    db.refresh(handoff)

    return {
        "handoff_id": handoff.id,
        "worker_id": worker.id,
        "task_id": handoff.task_id,
        "status": handoff.status,
    }


def _validate_workspace_consistency(db: Session, task: Any, summary: Dict) -> None:
    """A receiving worker must inspect files, not trust an old text summary."""
    if not isinstance(task, Task):
        return
    goal = db.query(Goal).filter(Goal.id == task.goal_id).first()
    root = os.path.realpath(goal.workspace_root or ".") if goal else None
    for item in summary.get("changed_files", []):
        path, expected = item.get("path"), item.get("checksum")
        if not path or not expected:
            continue
        resolved = os.path.realpath(path)
        if not root or os.path.commonpath([root, resolved]) != root or not os.path.isfile(resolved):
            raise HandoffConflictError("Workspace changed since handoff; receiving agent must replan")
        with open(resolved, "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
        if actual != expected:
            raise HandoffConflictError("Workspace file checksum differs from the handoff package")


def update_handoff_result(
    db: Session,
    handoff_id: str,
    result_after_handoff: str,
    result_note: Optional[str] = None,
) -> Dict:
    handoff = _get_handoff(db, handoff_id)
    if handoff.status != HANDOFF_STATUS_ACCEPTED:
        raise HandoffValidationError("Only accepted handoffs can be completed")

    handoff.result_after_handoff = result_after_handoff
    handoff.result_note = result_note
    _set_status(
        db,
        handoff,
        HANDOFF_STATUS_COMPLETED,
        f"Handoff completed with result: {result_after_handoff}",
    )

    task = _get_task(db, handoff.task_id)
    if isinstance(task, Task) and result_after_handoff == "success":
        from src.services import verifier_service

        if result_note:
            task.output = result_note
        verification = verifier_service.verify_task_contract(db, task)
        task.verification_status = verification["status"]
        if verification["status"] == "passed":
            task.status = "completed_verified"
            task.blocked_reason = None
        elif task.task_type in verifier_service.DETERMINISTIC_TASK_TYPES or task._get_json("acceptance_criteria"):
            task.status = "revision_required"
            task.blocked_reason = "Handoff reported success without passing the Completion Contract."
        elif (task.output or "").strip():
            task.status = "completed_unverified"
            task.blocked_reason = None
        else:
            task.status = "revision_required"
            task.blocked_reason = "Handoff reported success without a result artifact or output."
    elif task and result_after_handoff == "success":
        # Compatibility-only demo HandoffTask records are not executable
        # Runtime Tasks and therefore do not carry Completion Contracts.
        task.status = "completed"
    elif task and result_after_handoff == "failed":
        task.status = "failed"

    db.commit()
    db.refresh(handoff)
    return {
        "handoff_id": handoff.id,
        "status": handoff.status,
        "result_after_handoff": handoff.result_after_handoff,
    }


def _agent_labels(db: Session, agent_id: str) -> Tuple[Optional[str], Optional[str]]:
    agent = db.query(AgentStation).filter(AgentStation.id == agent_id).first()
    if not agent:
        return None, None
    return agent.name, agent.role


def _serialize_handoff(db: Session, handoff: HandoffRecord) -> Dict:
    data = handoff.to_dict()
    data["handoff_summary"] = _validate_summary(data.get("handoff_summary") or {})
    task = _get_task(db, handoff.task_id)
    worker = db.query(WorkerSession).filter(WorkerSession.id == handoff.to_worker_id).first() if handoff.to_worker_id else None
    from_name, from_role = _agent_labels(db, handoff.from_agent_id)
    to_name, to_role = _agent_labels(db, handoff.to_agent_id)
    data.update({
        "task": task.to_dict() if task else None,
        "from_agent_name": from_name,
        "from_agent_role": from_role,
        "to_agent_name": to_name,
        "to_agent_role": to_role,
        "worker": worker.to_dict() if worker else None,
    })
    return data


def _serialize_handoff_list_item(db: Session, handoff: HandoffRecord) -> Dict:
    task = _get_task(db, handoff.task_id)
    from_name, _ = _agent_labels(db, handoff.from_agent_id)
    to_name, _ = _agent_labels(db, handoff.to_agent_id)
    return {
        "id": handoff.id,
        "goal_id": handoff.goal_id,
        "task_id": handoff.task_id,
        "task_title": task.title if task else None,
        "from_agent_id": handoff.from_agent_id,
        "from_agent_name": from_name,
        "from_model_id": handoff.from_model_id,
        "to_agent_id": handoff.to_agent_id,
        "to_agent_name": to_name,
        "to_model_id": handoff.to_model_id,
        "reason": handoff.reason,
        "status": handoff.status,
        "result_after_handoff": handoff.result_after_handoff,
        "created_at": handoff.created_at.isoformat() if handoff.created_at else None,
    }
