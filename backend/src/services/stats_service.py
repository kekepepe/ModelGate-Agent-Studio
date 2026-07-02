from datetime import datetime, time, timedelta, timezone
from typing import Dict, List

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord
from src.models.model import Model
from src.models.quota import QuotaRecord
from src.models.tool import ToolCallRecord
from src.models.workspace import Goal, Task


ACTIVE_GOAL_STATUSES = {"idle", "queued", "running", "waiting", "reviewing", "handoff", "blocked"}
COMPLETED_STATUSES = {"completed", "done"}
FAILED_STATUSES = {"failed", "error"}


def _day_start(value: datetime) -> datetime:
    return datetime.combine(value.date(), time.min, tzinfo=timezone.utc)


def _today_window() -> tuple[datetime, datetime]:
    start = _day_start(datetime.now(timezone.utc))
    return start, start + timedelta(days=1)


def _date_key(value: datetime) -> str:
    return value.date().isoformat()


def _round_rate(value: float) -> float:
    return round(value, 4)


def get_dashboard_stats(db: Session) -> dict:
    today_start, tomorrow_start = _today_window()

    active_goals = db.query(Goal).filter(Goal.status.in_(ACTIVE_GOAL_STATUSES)).count()
    completed_goals_today = (
        db.query(Goal)
        .filter(Goal.status.in_(COMPLETED_STATUSES), Goal.updated_at >= today_start, Goal.updated_at < tomorrow_start)
        .count()
    )

    today_logs = db.query(ExecutionLog).filter(
        ExecutionLog.created_at >= today_start,
        ExecutionLog.created_at < tomorrow_start,
    )
    model_logs = today_logs.filter(ExecutionLog.event_type == "model_call")
    total_model_calls_today = model_logs.count()

    total_tokens_today = 0
    for log in model_logs.all():
        usage = log.get_token_usage()
        total_tokens_today += int(usage.get("total_tokens") or usage.get("total") or 0)

    total_tool_calls_today = (
        db.query(ToolCallRecord)
        .filter(ToolCallRecord.created_at >= today_start, ToolCallRecord.created_at < tomorrow_start)
        .count()
    )
    handoffs_today = (
        db.query(HandoffRecord)
        .filter(HandoffRecord.created_at >= today_start, HandoffRecord.created_at < tomorrow_start)
        .count()
    )

    agents_status = [
        {"agent_id": agent.id, "name": agent.name, "role": agent.role, "status": agent.status}
        for agent in db.query(AgentStation).order_by(AgentStation.name.asc()).all()
    ]

    models_by_id = {model.id: model for model in db.query(Model).all()}
    model_usage = []
    for quota in db.query(QuotaRecord).order_by(QuotaRecord.total_tokens.desc()).all():
        model = models_by_id.get(quota.model_id)
        model_usage.append(
            {
                "model_id": quota.model_id,
                "display_name": model.display_name if model else quota.model_name,
                "tokens_used": quota.total_tokens,
                "calls_count": quota.request_count,
            }
        )

    tool_usage = _get_tool_usage(db)
    recent_goals = [
        {"id": goal.id, "title": goal.title, "status": goal.status, "updated_at": goal.updated_at.isoformat() if goal.updated_at else None}
        for goal in db.query(Goal).order_by(Goal.updated_at.desc()).limit(5).all()
    ]

    return {
        "active_goals": active_goals,
        "completed_goals_today": completed_goals_today,
        "total_tokens_today": total_tokens_today,
        "total_model_calls_today": total_model_calls_today,
        "total_tool_calls_today": total_tool_calls_today,
        "handoffs_today": handoffs_today,
        "agents_status": agents_status,
        "model_usage": model_usage,
        "tool_usage": tool_usage,
        "recent_goals": recent_goals,
    }


def get_dashboard_trends(db: Session, days: int = 7) -> dict:
    safe_days = min(max(days, 1), 30)
    today = _day_start(datetime.now(timezone.utc))
    start = today - timedelta(days=safe_days - 1)
    end = today + timedelta(days=1)

    daily: Dict[str, dict] = {}
    for offset in range(safe_days):
        key = (start + timedelta(days=offset)).date().isoformat()
        daily[key] = {
            "date": key,
            "tokens": 0,
            "model_calls": 0,
            "tool_calls": 0,
            "handoffs": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "quota_usage_percent": 0.0,
        }

    for log in db.query(ExecutionLog).filter(ExecutionLog.created_at >= start, ExecutionLog.created_at < end).all():
        key = _date_key(log.created_at)
        if key not in daily:
            continue
        if log.event_type == "model_call":
            daily[key]["model_calls"] += 1
            usage = log.get_token_usage()
            daily[key]["tokens"] += int(usage.get("total_tokens") or usage.get("total") or 0)

    for call in db.query(ToolCallRecord).filter(ToolCallRecord.created_at >= start, ToolCallRecord.created_at < end).all():
        key = _date_key(call.created_at)
        if key in daily:
            daily[key]["tool_calls"] += 1

    for handoff in db.query(HandoffRecord).filter(HandoffRecord.created_at >= start, HandoffRecord.created_at < end).all():
        key = _date_key(handoff.created_at)
        if key in daily:
            daily[key]["handoffs"] += 1

    for task in db.query(Task).filter(Task.updated_at >= start, Task.updated_at < end).all():
        key = _date_key(task.updated_at)
        if key not in daily:
            continue
        if task.status in COMPLETED_STATUSES:
            daily[key]["tasks_completed"] += 1
        elif task.status in FAILED_STATUSES:
            daily[key]["tasks_failed"] += 1

    quota_records = db.query(QuotaRecord).all()
    avg_quota_usage = 0.0
    records_with_usage = [record.usage_percent for record in quota_records if record.usage_percent is not None]
    if records_with_usage:
        avg_quota_usage = round((sum(records_with_usage) / len(records_with_usage)) * 100, 2)
    for item in daily.values():
        item["quota_usage_percent"] = avg_quota_usage

    return {"daily": list(daily.values())}


def get_agent_performance(db: Session) -> dict:
    agents = db.query(AgentStation).order_by(AgentStation.name.asc()).all()
    result: List[dict] = []

    for agent in agents:
        tasks = db.query(Task).filter(Task.assigned_agent_id == agent.id).all()
        completed_tasks = [task for task in tasks if task.status in COMPLETED_STATUSES]
        failed_tasks = [task for task in tasks if task.status in FAILED_STATUSES]

        completed = len(completed_tasks) if tasks else agent.total_tasks_completed
        failed = len(failed_tasks) if tasks else agent.total_tasks_failed
        total = completed + failed
        success_rate = _round_rate(completed / total) if total else 0.0

        token_values = [task.tokens_used for task in tasks if task.tokens_used is not None]
        duration_values = [task.duration_ms for task in tasks if task.duration_ms is not None]
        avg_tokens = int(sum(token_values) / len(token_values)) if token_values else (agent.average_tokens_per_task or 0)
        avg_duration = int(sum(duration_values) / len(duration_values)) if duration_values else 0

        handoffs = db.query(HandoffRecord).filter(HandoffRecord.from_agent_id == agent.id).count()
        result.append(
            {
                "agent_id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "tasks_completed": completed,
                "tasks_failed": failed,
                "success_rate": success_rate,
                "avg_tokens_per_task": avg_tokens,
                "avg_duration_ms": avg_duration,
                "total_handoffs_initiated": handoffs or agent.total_handoffs_initiated,
            }
        )

    return {"agents": result}


def _get_tool_usage(db: Session) -> List[dict]:
    rows = (
        db.query(
            ToolCallRecord.tool_name,
            func.count(ToolCallRecord.id).label("call_count"),
            func.sum(case((ToolCallRecord.status == "completed", 1), else_=0)).label("success_count"),
        )
        .group_by(ToolCallRecord.tool_name)
        .order_by(func.count(ToolCallRecord.id).desc())
        .all()
    )

    result = []
    for row in rows:
        call_count = int(row.call_count or 0)
        success_count = int(row.success_count or 0)
        failed_count = max(call_count - success_count, 0)
        result.append(
            {
                "tool_name": row.tool_name,
                "call_count": call_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": _round_rate(success_count / call_count) if call_count else 0.0,
            }
        )
    return result
