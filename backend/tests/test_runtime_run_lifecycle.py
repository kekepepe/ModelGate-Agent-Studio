import uuid

from src.models.workspace import Goal, RuntimeRun, Task
from src.services import runtime_service


def test_pause_and_resume_persist_runtime_run(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Resumable", status="running", execution_mode="mock")
    db_session.add(goal)
    db_session.commit()
    run = runtime_service._get_or_start_run(db_session, goal)

    paused = runtime_service.pause_goal_run(db_session, goal.id)
    db_session.refresh(goal)
    db_session.refresh(run)
    assert paused["status"] == "paused"
    assert goal.status == "paused"
    assert run.status == "paused"

    resumed = runtime_service.resume_goal_run(db_session, goal.id)
    db_session.refresh(goal)
    db_session.refresh(run)
    assert resumed["status"] == "running"
    assert goal.status == "running"
    assert run.status == "running"


def test_pipeline_keeps_pause_state_after_current_task_returns(db_session, monkeypatch):
    goal = Goal(id=str(uuid.uuid4()), title="Pause during task", status="running", execution_mode="mock")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Current task", status="pending")
    db_session.add_all([goal, task])
    db_session.commit()

    calls = {"count": 0}

    def ready_tasks(_db, _goal_id):
        calls["count"] += 1
        return [task] if calls["count"] == 1 else []

    def finish_current_task_and_pause(db, executing_task):
        executing_goal = db.query(Goal).filter(Goal.id == executing_task.goal_id).one()
        executing_goal.status = "paused"
        db.commit()
        return {"status": "completed", "tokens_used": 0, "duration_ms": 0}

    from src.services import orchestrator_service
    monkeypatch.setattr(orchestrator_service, "ready_tasks", ready_tasks)
    monkeypatch.setattr(runtime_service, "_execute_single_task", finish_current_task_and_pause)

    result = runtime_service.execute_goal_pipeline(db_session, goal.id)
    db_session.refresh(goal)
    run = db_session.query(RuntimeRun).filter(RuntimeRun.id == goal.run_id).one()
    assert result["status"] == "paused"
    assert goal.status == "paused"
    assert run.status == "paused"


def test_stop_cancels_run_and_unfinished_tasks(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Stop me", status="running", execution_mode="mock")
    pending = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Pending", status="pending")
    completed = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Done", status="completed")
    db_session.add_all([goal, pending, completed])
    db_session.commit()
    run = runtime_service._get_or_start_run(db_session, goal)

    result = runtime_service.stop_goal_run(db_session, goal.id)
    db_session.refresh(goal)
    db_session.refresh(run)
    db_session.refresh(pending)
    db_session.refresh(completed)

    assert result["status"] == "cancelled"
    assert goal.status == "cancelled"
    assert run.status == "cancelled"
    assert pending.status == "cancelled"
    assert completed.status == "completed"
