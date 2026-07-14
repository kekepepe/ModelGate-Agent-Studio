from typing import Dict, List

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord, WorkerSession
from src.models.model import Model
from src.models.quota import QuotaRecord
from src.models.workspace import Goal, Task


class WorkspaceNotFoundError(Exception):
    pass


def get_workspace_state(db: Session, goal_id: str) -> Dict:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise WorkspaceNotFoundError(f"Goal '{goal_id}' not found")

    # Runtime executes the current MVP plan serially, so return the persisted
    # creation order as the same order rendered by the Workspace task flow.
    tasks = (
        db.query(Task)
        .filter(Task.goal_id == goal_id)
        .order_by(Task.created_at.asc(), Task.id.asc())
        .all()
    )

    # All registered agents
    agents = db.query(AgentStation).filter(AgentStation.is_enabled == True).all()

    # Workers related to this goal
    workers = db.query(WorkerSession).filter(WorkerSession.goal_id == goal_id).all()
    handoff_records = (
        db.query(HandoffRecord)
        .filter(HandoffRecord.goal_id == goal_id)
        .order_by(HandoffRecord.created_at.asc())
        .all()
    )

    task_ids = {task.id for task in tasks}
    recent_logs = []
    if task_ids:
        # One bounded query feeds the task detail panels and avoids a polling
        # waterfall of /logs and /router requests for every visible card.
        recent_logs = (
            db.query(ExecutionLog)
            .filter(ExecutionLog.task_id.in_(task_ids))
            .order_by(ExecutionLog.created_at.desc())
            .limit(max(len(task_ids) * 12, 12))
            .all()
        )

    latest_worker_by_task: Dict[str, WorkerSession] = {}
    for worker in workers:
        existing = latest_worker_by_task.get(worker.task_id)
        if not existing or (worker.created_at and existing.created_at and worker.created_at > existing.created_at):
            latest_worker_by_task[worker.task_id] = worker

    model_ids = {w.model_id for w in workers if w.model_id}
    models = {}
    if model_ids:
        db_models = db.query(Model).filter(Model.id.in_(model_ids)).all()
        models = {m.id: m.display_name for m in db_models}

    quota_by_model = {}
    if model_ids:
        quota_records = db.query(QuotaRecord).filter(QuotaRecord.model_id.in_(model_ids)).all()
        quota_by_model = {record.model_id: _serialize_quota(record) for record in quota_records}

    logs_by_task: Dict[str, List[ExecutionLog]] = {}
    for log in recent_logs:
        if log.task_id and len(logs_by_task.setdefault(log.task_id, [])) < 10:
            logs_by_task[log.task_id].append(log)

    agent_labels = {a.id: {"name": a.name, "role": a.role} for a in agents}
    handoffs = [_serialize_workspace_handoff(record, agent_labels) for record in handoff_records]
    handoffs_by_task: Dict[str, List[Dict]] = {}
    for handoff in handoffs:
        handoffs_by_task.setdefault(handoff["task_id"], []).append(handoff)

    task_data = []
    for flow_position, task in enumerate(tasks, start=1):
        item = task.to_dict()
        item["flow_position"] = flow_position
        timeline = handoffs_by_task.get(task.id, [])
        worker = latest_worker_by_task.get(task.id)
        task_logs = logs_by_task.get(task.id, [])
        routing_decision = next(
            (log.get_routing_info() for log in task_logs if log.get_routing_info()),
            None,
        )
        item["handoffs"] = timeline
        item["handoff"] = timeline[-1] if timeline else None
        item["worker_status"] = worker.status if worker else None
        item["model_id"] = worker.model_id if worker else None
        item["model_name"] = models.get(worker.model_id) if worker else None
        item["quota"] = quota_by_model.get(worker.model_id) if worker else None
        item["routing_decision"] = routing_decision
        item["context"] = worker.current_context if worker else None
        item["recent_logs"] = [_serialize_workspace_log(log, models, agent_labels) for log in task_logs]
        task_data.append(item)

    return {
        "goal": goal.to_dict() if goal else None,
        "tasks": task_data,
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role,
                "status": a.status,
                "default_model_id": a.default_model_id,
                "is_enabled": a.is_enabled,
            }
            for a in agents
        ],
        "workers": [
            {
                "id": w.id,
                "agent_id": w.agent_id,
                "model_id": w.model_id,
                "goal_id": w.goal_id,
                "task_id": w.task_id,
                "inherited_from_handoff_id": w.inherited_from_handoff_id,
                "status": w.status,
                "total_tokens_used": w.total_tokens_used,
                "model_name": models.get(w.model_id) if w.model_id else None,
            }
            for w in workers
        ],
        "handoffs": handoffs,
    }


def _serialize_workspace_handoff(record: HandoffRecord, agent_labels: Dict[str, Dict[str, str]]) -> Dict:
    """A compact, task-oriented handoff timeline for the Workspace state payload."""
    from_agent = agent_labels.get(record.from_agent_id, {})
    to_agent = agent_labels.get(record.to_agent_id, {})
    return {
        "id": record.id,
        "task_id": record.task_id,
        "status": record.status,
        "reason": record.reason,
        "reason_description": record.reason_description,
        "from_agent_id": record.from_agent_id,
        "from_agent_name": from_agent.get("name"),
        "from_model_id": record.from_model_id,
        "to_agent_id": record.to_agent_id,
        "to_agent_name": to_agent.get("name"),
        "to_model_id": record.to_model_id,
        "result_after_handoff": record.result_after_handoff,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "accepted_at": record.accepted_at.isoformat() if record.accepted_at else None,
        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
    }


def _serialize_quota(record: QuotaRecord) -> Dict:
    return {
        "model_id": record.model_id,
        "quota_status": record.quota_status,
        "usage_percent": record.usage_percent,
        "estimated_remaining": record.estimated_remaining,
        "total_tokens": record.total_tokens,
        "token_limit": record.token_limit,
        "request_count": record.request_count,
    }


def _serialize_workspace_log(log: ExecutionLog, models: Dict[str, str], agent_labels: Dict[str, Dict[str, str]]) -> Dict:
    return {
        "id": log.id,
        "event_type": log.event_type,
        "event_status": log.event_status,
        "output_summary": log.output_summary,
        "input_summary": log.input_summary,
        "error_message": log.error_message,
        "quota_status": log.quota_status,
        "model_id": log.model_id,
        "model_name": models.get(log.model_id),
        "agent_id": log.agent_id,
        "agent_name": agent_labels.get(log.agent_id, {}).get("name"),
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
