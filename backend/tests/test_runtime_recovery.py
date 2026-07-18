import uuid
from datetime import datetime, timedelta, timezone

from src.models.handoff import WorkerSession
from src.models.tool import ToolCallRecord
from src.models.workspace import Goal, Task
from src.services.recovery_service import recover_interrupted_tasks


def _expired_task(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Recover", status="running")
    task = Task(
        id=str(uuid.uuid4()),
        goal_id=goal.id,
        title="Interrupted",
        status="running",
        lease_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    worker = WorkerSession(
        id=str(uuid.uuid4()),
        agent_id="agent",
        model_id="model",
        goal_id=goal.id,
        task_id=task.id,
        status="running",
    )
    task.assigned_worker_id = worker.id
    db_session.add_all([goal, task, worker])
    db_session.commit()
    return goal, task, worker


def test_expired_task_becomes_recoverable_and_verified_tasks_are_untouched(db_session):
    goal, task, worker = _expired_task(db_session)
    verified = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Done", status="completed_verified")
    db_session.add(verified)
    db_session.commit()

    result = recover_interrupted_tasks(db_session, goal.id)

    db_session.refresh(task)
    db_session.refresh(worker)
    db_session.refresh(verified)
    assert result == {"recovered": 1, "approval_required": 0}
    assert task.status == "pending"
    assert task.recovery_count == 1
    assert worker.status == "recoverable"
    assert verified.status == "completed_verified"


def test_non_idempotent_completed_tool_requires_approval(db_session):
    goal, task, _worker = _expired_task(db_session)
    db_session.add(ToolCallRecord(
        id=str(uuid.uuid4()),
        goal_id=goal.id,
        task_id=task.id,
        tool_name="terminal_execute",
        status="completed",
        idempotency_key=None,
    ))
    db_session.commit()

    result = recover_interrupted_tasks(db_session, goal.id)

    db_session.refresh(task)
    assert result == {"recovered": 0, "approval_required": 1}
    assert task.status == "waiting_approval"
