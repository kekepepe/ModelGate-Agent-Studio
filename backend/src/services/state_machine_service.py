"""Runtime status invariants and atomic status/event transitions."""

from datetime import datetime, timezone
from typing import Dict, Optional, Set

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from src.models.workspace import Goal, Task
from src.services import log_service


class InvalidStateTransition(ValueError):
    pass


GOAL_TRANSITIONS: Dict[str, Set[str]] = {
    "idle": {"planning", "cancelled"},
    "draft": {"planning", "cancelled"},
    "planning": {"waiting_confirmation", "running", "paused", "replanning", "blocked", "failed", "cancelled"},
    "waiting_confirmation": {"running", "replanning", "cancelled"},
    "running": {"paused", "waiting_approval", "revision_required", "replanning", "blocked", "handoff", "completed", "failed", "cancelled"},
    "reviewing": {"paused", "revision_required", "replanning", "completed", "failed", "cancelled"},
    "paused": {"planning", "running", "cancelled"},
    "waiting_approval": {"running", "blocked", "cancelled"},
    "revision_required": {"running", "replanning", "failed", "cancelled"},
    "replanning": {"planning", "waiting_confirmation", "running", "completed", "blocked", "failed", "cancelled"},
    "handoff": {"running", "blocked", "failed", "cancelled"},
    "blocked": {"running", "replanning", "failed", "cancelled"},
    "completed": {"revision_required", "replanning"},
    "failed": {"planning", "cancelled"},
    "cancelled": set(),
}

TASK_TRANSITIONS: Dict[str, Set[str]] = {
    "pending": {"ready", "assigned", "running", "waiting_approval", "blocked", "skipped", "cancelled", "failed", "handoff"},
    "ready": {"assigned", "running", "waiting_approval", "blocked", "skipped", "cancelled", "failed", "handoff"},
    "assigned": {"running", "waiting_approval", "blocked", "cancelled", "failed", "handoff"},
    "running": {"pending", "waiting_approval", "completed", "completed_verified", "completed_unverified", "revision_required", "replanning", "blocked", "cancelled", "failed", "handoff"},
    "waiting_approval": {"pending", "blocked", "skipped", "cancelled"},
    "completed_unverified": {"pending", "revision_required", "cancelled"},
    "revision_required": {"pending", "replanning", "blocked", "cancelled", "failed"},
    "replanning": {"pending", "ready", "cancelled"},
    "blocked": {"pending", "replanning", "cancelled", "failed"},
    "failed": {"pending", "handoff", "cancelled"},
    "handoff": {"running", "completed", "completed_verified", "completed_unverified", "revision_required", "blocked", "failed", "cancelled"},
    "completed": set(),
    "completed_verified": set(),
    "skipped": set(),
    "cancelled": {"pending"},
}


def validate_transition(kind: str, current: str, target: str) -> None:
    transitions = GOAL_TRANSITIONS if kind == "goal" else TASK_TRANSITIONS
    if current == target:
        return
    if current not in transitions or target not in transitions[current]:
        raise InvalidStateTransition(f"Illegal {kind} state transition: {current} -> {target}")


def transition_goal(
    db: Session,
    goal: Goal,
    target: str,
    *,
    summary: str,
    event_type: str = "goal_status_change",
    event_status: Optional[str] = None,
) -> Goal:
    validate_transition("goal", goal.status, target)
    try:
        goal.status = target
        goal.updated_at = datetime.now(timezone.utc)
        log_service.create_log(db, {
            "goal_id": goal.id,
            "event_type": event_type,
            "event_status": event_status or target,
            "output_summary": summary,
        }, commit=False)
        db.commit()
        db.refresh(goal)
        return goal
    except Exception:
        db.rollback()
        raise


def transition_task(
    db: Session,
    task: Task,
    target: str,
    *,
    summary: str,
    event_type: str = "task_status_change",
    event_status: Optional[str] = None,
) -> Task:
    validate_transition("task", task.status, target)
    try:
        task.status = target
        task.updated_at = datetime.now(timezone.utc)
        log_service.create_log(db, {
            "goal_id": task.goal_id,
            "task_id": task.id,
            "event_type": event_type,
            "event_status": event_status or target,
            "output_summary": summary,
        }, commit=False)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


_installed = False


def install_state_guards() -> None:
    global _installed
    if _installed:
        return

    @event.listens_for(Session, "before_flush")
    def reject_illegal_transitions(session, _flush_context, _instances):
        for entity in session.dirty:
            if not isinstance(entity, (Goal, Task)):
                continue
            history = inspect(entity).attrs.status.history
            if not history.has_changes() or not history.deleted or not history.added:
                continue
            validate_transition(
                "goal" if isinstance(entity, Goal) else "task",
                history.deleted[0],
                history.added[0],
            )

    _installed = True
