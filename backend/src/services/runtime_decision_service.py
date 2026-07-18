"""One decision vocabulary shared by retry, revise, handoff, replan and blocking paths."""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.workspace import Task
from src.schemas.planning import RuntimeDecisionContract
from src.services import log_service


def decide_failure(
    task: Task,
    *,
    trigger: str,
    reason: str,
    retry_available: bool = False,
    handoff_available: bool = False,
    ask_user: bool = False,
    evidence: Optional[List[dict]] = None,
) -> RuntimeDecisionContract:
    if ask_user:
        action = "ask_user"
    elif retry_available:
        action = "revise_current_task"
    elif handoff_available:
        action = "handoff"
    elif trigger in {
        "tool_failure",
        "verification_failure",
        "context_invalidated",
        "workspace_conflict",
        "handoff_context_missing",
        "user_change",
    }:
        action = "replan_graph"
    else:
        action = "blocked"
    return RuntimeDecisionContract(
        action=action,
        reason=reason,
        evidence=[{"trigger": trigger}, *(evidence or [])],
        task_id=task.id,
    )


def record_decision(db: Session, task: Task, decision: RuntimeDecisionContract) -> None:
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "event_type": "runtime.decision",
        "event_status": decision.action,
        "output_summary": decision.reason,
        "metadata": decision.model_dump(),
    })


def record_goal_decision(db: Session, goal_id: str, decision: RuntimeDecisionContract) -> None:
    log_service.create_log(db, {
        "goal_id": goal_id,
        "task_id": decision.task_id,
        "event_type": "runtime.decision",
        "event_status": decision.action,
        "output_summary": decision.reason,
        "metadata": decision.model_dump(),
    })
