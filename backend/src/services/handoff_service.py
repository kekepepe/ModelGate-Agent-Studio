from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord, HandoffTask, WorkerSession
from src.models.model import Model
from src.schemas.handoff import HandoffTaskCreate

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
]

LOG_ACTION_BY_STATUS = {
    HANDOFF_STATUS_REQUESTED: "handoff_requested",
    HANDOFF_STATUS_GENERATING: "handoff_summary_generating",
    HANDOFF_STATUS_READY: "handoff_summary_ready",
    HANDOFF_STATUS_ACCEPTED: "handoff_accepted",
    HANDOFF_STATUS_COMPLETED: "handoff_completed",
    HANDOFF_STATUS_FAILED: "handoff_failed",
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

    _create_log(
        db,
        handoff=handoff,
        action=LOG_ACTION_BY_STATUS[next_status],
        level="error" if next_status == HANDOFF_STATUS_FAILED else "handoff",
        message=message or f"Handoff status changed to {next_status}",
    )


def _validate_summary(summary: Dict) -> Dict:
    normalized = {}
    for field in REQUIRED_SUMMARY_FIELDS:
        value = summary.get(field)
        if field in {"original_goal", "current_task"}:
            normalized[field] = value if isinstance(value, str) and value else "—"
        else:
            normalized[field] = value if isinstance(value, list) else []
    return normalized


def _build_fallback_summary(
    task: HandoffTask,
    from_agent: AgentStation,
    to_agent: AgentStation,
    reason: str,
    reason_description: Optional[str] = None,
) -> Dict:
    completed_work = []
    if task.current_output:
        completed_work.append(task.current_output)
    else:
        completed_work.append("已保留当前任务上下文，等待接手 Agent 继续推进。")

    risks = []
    if task.error_message:
        risks.append(task.error_message)
    if reason_description:
        risks.append(reason_description)
    if not risks:
        risks.append("当前未记录明确错误，交接原因来自用户或系统判断。")

    return _validate_summary({
        "original_goal": f"Goal {task.goal_id}",
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
    })


def _create_log(
    db: Session,
    handoff: HandoffRecord,
    action: str,
    level: str,
    message: str,
    agent_id: Optional[str] = None,
    worker_id: Optional[str] = None,
    model_id: Optional[str] = None,
) -> ExecutionLog:
    log = ExecutionLog(
        goal_id=handoff.goal_id,
        task_id=handoff.task_id,
        agent_id=agent_id or handoff.from_agent_id,
        worker_id=worker_id or handoff.from_worker_id,
        model_id=model_id or handoff.from_model_id,
        handoff_id=handoff.id,
        level=level,
        action=action,
        message=message,
    )
    db.add(log)
    return log


def _get_task(db: Session, task_id: str) -> HandoffTask:
    task = db.query(HandoffTask).filter(HandoffTask.id == task_id).first()
    if not task:
        raise HandoffNotFoundError(f"Task '{task_id}' not found")
    return task


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

    if task.status not in {"running", "failed", "handoff"}:
        raise HandoffValidationError("Task status must be running or failed to trigger handoff")

    from_agent = _get_agent(db, task.assigned_agent_id)
    to_agent = _get_agent(db, to_agent_id)
    resolved_to_model_id = _resolve_model_id(db, to_agent, to_model_id)

    handoff = HandoffRecord(
        goal_id=task.goal_id,
        task_id=task.id,
        from_agent_id=task.assigned_agent_id,
        from_model_id=task.assigned_model_id,
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
        action="handoff_requested",
        level="handoff",
        message=f"Handoff requested: {from_agent.name} -> {to_agent.name} ({reason})",
    )

    _set_status(db, handoff, HANDOFF_STATUS_GENERATING, "Generating handoff summary")
    summary = _build_fallback_summary(task, from_agent, to_agent, reason, reason_description)
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
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def accept_handoff(db: Session, handoff_id: str, agent_id: Optional[str] = None, model_id: Optional[str] = None) -> Dict:
    handoff = _get_handoff(db, handoff_id)
    if handoff.status != HANDOFF_STATUS_READY:
        raise HandoffValidationError("Only ready handoffs can be accepted")

    accept_agent_id = agent_id or handoff.to_agent_id
    accept_model_id = model_id or handoff.to_model_id
    agent = _get_agent(db, accept_agent_id)
    _resolve_model_id(db, agent, accept_model_id)
    task = _get_task(db, handoff.task_id)

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
    task.assigned_model_id = accept_model_id
    task.assigned_worker_id = worker.id
    agent.status = "running"

    if handoff.from_worker_id:
        previous_worker = db.query(WorkerSession).filter(WorkerSession.id == handoff.from_worker_id).first()
        if previous_worker:
            previous_worker.status = "handoff_required"

    _set_status(db, handoff, HANDOFF_STATUS_ACCEPTED, "Handoff accepted and worker session created")
    _create_log(
        db,
        handoff=handoff,
        action="handoff_worker_created",
        level="exec",
        message="New worker session created from handoff",
        agent_id=accept_agent_id,
        worker_id=worker.id,
        model_id=accept_model_id,
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

    task = db.query(HandoffTask).filter(HandoffTask.id == handoff.task_id).first()
    if task and result_after_handoff == "success":
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


def list_logs(db: Session, handoff_id: Optional[str] = None) -> List[Dict]:
    query = db.query(ExecutionLog)
    if handoff_id:
        query = query.filter(ExecutionLog.handoff_id == handoff_id)
    return [log.to_dict() for log in query.order_by(ExecutionLog.created_at.asc()).all()]


def _agent_labels(db: Session, agent_id: str) -> Tuple[Optional[str], Optional[str]]:
    agent = db.query(AgentStation).filter(AgentStation.id == agent_id).first()
    if not agent:
        return None, None
    return agent.name, agent.role


def _serialize_handoff(db: Session, handoff: HandoffRecord) -> Dict:
    data = handoff.to_dict()
    data["handoff_summary"] = _validate_summary(data.get("handoff_summary") or {})
    task = db.query(HandoffTask).filter(HandoffTask.id == handoff.task_id).first()
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
    task = db.query(HandoffTask).filter(HandoffTask.id == handoff.task_id).first()
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
