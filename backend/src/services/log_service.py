import json
import uuid
from datetime import datetime, timezone
from math import ceil
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffTask
from src.models.model import Model


class LogNotFoundError(Exception):
    pass


class LogValidationError(Exception):
    pass


def create_log(db: Session, data: Dict[str, Any]) -> ExecutionLog:
    log = ExecutionLog(
        id=str(uuid.uuid4()),
        goal_id=data.get("goal_id"),
        task_id=data.get("task_id"),
        agent_id=data.get("agent_id"),
        worker_id=data.get("worker_id"),
        model_id=data.get("model_id"),
        handoff_id=data.get("handoff_id"),
        event_type=data.get("event_type", "agent_step"),
        event_status=data.get("event_status", "info"),
        input_summary=data.get("input_summary"),
        output_summary=data.get("output_summary"),
        latency_ms=data.get("latency_ms"),
        error_type=data.get("error_type"),
        error_code=data.get("error_code"),
        error_message=data.get("error_message"),
        tool_name=data.get("tool_name"),
        quota_status=data.get("quota_status"),
        handoff_status=data.get("handoff_status"),
    )
    if data.get("token_usage"):
        log.set_token_usage(data["token_usage"])
    if data.get("metadata"):
        log.set_metadata(data["metadata"])
    if data.get("routing_info"):
        log.set_routing_info(data["routing_info"])
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_log(db: Session, log_id: str) -> Dict[str, Any]:
    log = db.query(ExecutionLog).filter(ExecutionLog.id == log_id).first()
    if not log:
        raise LogNotFoundError(f"Log '{log_id}' not found")
    return _enrich_log(db, log)


def list_logs(
    db: Session,
    goal_id: Optional[str] = None,
    task_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    model_id: Optional[str] = None,
    handoff_id: Optional[str] = None,
    event_type: Optional[str] = None,
    event_status: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    query = db.query(ExecutionLog)

    if goal_id:
        query = query.filter(ExecutionLog.goal_id == goal_id)
    if task_id:
        query = query.filter(ExecutionLog.task_id == task_id)
    if agent_id:
        query = query.filter(ExecutionLog.agent_id == agent_id)
    if model_id:
        query = query.filter(ExecutionLog.model_id == model_id)
    if handoff_id:
        query = query.filter(ExecutionLog.handoff_id == handoff_id)
    if event_type:
        types = [t.strip() for t in event_type.split(",") if t.strip()]
        if len(types) == 1:
            query = query.filter(ExecutionLog.event_type == types[0])
        elif len(types) > 1:
            query = query.filter(ExecutionLog.event_type.in_(types))
    if event_status:
        statuses = [s.strip() for s in event_status.split(",") if s.strip()]
        if len(statuses) == 1:
            query = query.filter(ExecutionLog.event_status == statuses[0])
        elif len(statuses) > 1:
            query = query.filter(ExecutionLog.event_status.in_(statuses))
    if start_time:
        query = query.filter(ExecutionLog.created_at >= start_time)
    if end_time:
        query = query.filter(ExecutionLog.created_at <= end_time)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                ExecutionLog.input_summary.ilike(like),
                ExecutionLog.output_summary.ilike(like),
                ExecutionLog.error_message.ilike(like),
            )
        )

    total = query.count()
    logs = query.order_by(ExecutionLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [_enrich_log(db, log) for log in logs]
    total_pages = ceil(total / page_size) if page_size > 0 else 0
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}


def get_task_timeline(db: Session, task_id: str) -> Dict[str, Any]:
    logs = (
        db.query(ExecutionLog)
        .filter(ExecutionLog.task_id == task_id)
        .order_by(ExecutionLog.created_at.asc())
        .all()
    )

    events = []
    total_tokens = 0
    model_call_count = 0
    handoff_count = 0
    error_count = 0

    for log in logs:
        token_usage = log.get_token_usage()
        tokens = token_usage.get("total_tokens", 0) if token_usage else 0
        total_tokens += tokens

        if log.event_type == "model_call":
            model_call_count += 1
        if log.event_type in ("handoff_created", "handoff_completed"):
            handoff_count += 1
        if log.event_status in ("error", "failed"):
            error_count += 1

        summary = log.output_summary or log.input_summary or log.error_message or log.event_type
        events.append({
            "time": log.created_at.isoformat() if log.created_at else "",
            "event_type": log.event_type,
            "event_status": log.event_status,
            "agent_id": log.agent_id,
            "model_id": log.model_id,
            "summary": summary,
            "icon_type": log.event_type,
        })

    total_duration_ms = 0
    if len(logs) >= 2 and logs[0].created_at and logs[-1].created_at:
        total_duration_ms = int((logs[-1].created_at - logs[0].created_at).total_seconds() * 1000)

    return {
        "events": events,
        "summary": {
            "total_duration_ms": total_duration_ms,
            "total_tokens": total_tokens,
            "model_call_count": model_call_count,
            "handoff_count": handoff_count,
            "error_count": error_count,
        },
    }


def _agent_name(db: Session, agent_id: Optional[str]) -> Optional[str]:
    if not agent_id:
        return None
    agent = db.query(AgentStation).filter(AgentStation.id == agent_id).first()
    return agent.name if agent else None


def _task_title(db: Session, task_id: Optional[str]) -> Optional[str]:
    if not task_id:
        return None
    task = db.query(HandoffTask).filter(HandoffTask.id == task_id).first()
    return task.title if task else None


def _model_name(db: Session, model_id: Optional[str]) -> Optional[str]:
    if not model_id:
        return None
    model = db.query(Model).filter(Model.id == model_id).first()
    return model.display_name if model else None


def _enrich_log(db: Session, log: ExecutionLog) -> Dict[str, Any]:
    data = log.to_dict()
    data["agent_name"] = _agent_name(db, log.agent_id)
    data["task_title"] = _task_title(db, log.task_id)
    data["model_name"] = _model_name(db, log.model_id)
    return data
