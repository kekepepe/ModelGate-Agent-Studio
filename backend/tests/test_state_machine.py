import uuid

import pytest

from src.models.handoff import ExecutionLog
from src.models.workspace import Goal, Task
from src.services import log_service
from src.services.state_machine_service import (
    InvalidStateTransition,
    transition_goal,
    transition_task,
    validate_transition,
)


def test_illegal_terminal_transition_is_rejected():
    with pytest.raises(InvalidStateTransition, match="completed_verified -> running"):
        validate_transition("task", "completed_verified", "running")
    with pytest.raises(InvalidStateTransition, match="completed -> running"):
        validate_transition("goal", "completed", "running")


def test_task_state_and_event_commit_together(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Atomic", status="running")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Task", status="pending")
    db_session.add_all([goal, task])
    db_session.commit()

    transition_task(db_session, task, "ready", summary="Dependencies complete")

    assert task.status == "ready"
    event = db_session.query(ExecutionLog).filter(ExecutionLog.task_id == task.id).one()
    assert event.event_status == "ready"


def test_transition_rolls_back_when_event_write_fails(db_session, monkeypatch):
    goal = Goal(id=str(uuid.uuid4()), title="Rollback", status="idle")
    db_session.add(goal)
    db_session.commit()

    def fail_log(*_args, **_kwargs):
        raise RuntimeError("log storage failed")

    monkeypatch.setattr(log_service, "create_log", fail_log)
    with pytest.raises(RuntimeError, match="log storage failed"):
        transition_goal(db_session, goal, "planning", summary="start")

    db_session.refresh(goal)
    assert goal.status == "idle"
