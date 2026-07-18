import uuid

from src.models.handoff import ExecutionLog
from src.models.workspace import Goal, Task
from src.models.agent import AgentStation
from src.services import scheduler_service, task_service


def _goal(db_session, **overrides):
    values = {
        "id": str(uuid.uuid4()),
        "title": "Scheduler",
        "status": "running",
        "execution_mode": "mock",
    }
    values.update(overrides)
    goal = Goal(**values)
    db_session.add(goal)
    db_session.commit()
    return goal


def _task(db_session, goal, title, dependencies=None, status="pending", parallel=False):
    task = Task(
        id=str(uuid.uuid4()),
        goal_id=goal.id,
        title=title,
        status=status,
        priority=10,
    )
    task.set_json("dependencies", dependencies or [])
    task.set_json("required_capabilities", ["parallel_safe"] if parallel else [])
    db_session.add(task)
    db_session.commit()
    return task


def test_scheduler_blocks_missing_dependency_with_explicit_evidence(db_session):
    goal = _goal(db_session)
    task = _task(db_session, goal, "Broken", ["missing-task"])
    decision = scheduler_service.schedule_ready_tasks(db_session, goal)
    db_session.refresh(task)

    assert decision.goal_status == "blocked"
    assert decision.invalid_task_ids == [task.id]
    assert "Missing dependencies" in decision.blocked_reason
    assert task.status == "blocked"
    event = db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "task.blocked",
    ).one()
    assert "missing-task" in event.output_summary


def test_scheduler_blocks_every_task_in_dependency_cycle(db_session):
    goal = _goal(db_session)
    left = _task(db_session, goal, "Left")
    right = _task(db_session, goal, "Right", [left.id])
    left.set_json("dependencies", [right.id])
    db_session.commit()

    decision = scheduler_service.schedule_ready_tasks(db_session, goal)
    db_session.refresh(left)
    db_session.refresh(right)
    assert set(decision.invalid_task_ids) == {left.id, right.id}
    assert left.status == right.status == "blocked"
    assert "Dependency cycle" in decision.blocked_reason


def test_scheduler_respects_parallel_limit_and_logs_group(db_session):
    goal = _goal(db_session, max_parallel_tasks=2)
    tasks = [_task(db_session, goal, f"Parallel {index}", parallel=True) for index in range(3)]
    decision = scheduler_service.schedule_ready_tasks(db_session, goal)

    assert len(decision.ready_tasks) == 3
    assert len(decision.selected_tasks) == 2
    assert set(item.id for item in decision.selected_tasks).issubset({item.id for item in tasks})
    event = db_session.query(ExecutionLog).filter(
        ExecutionLog.goal_id == goal.id,
        ExecutionLog.event_type == "task.parallel_group_started",
    ).one()
    assert event.get_metadata()["max_parallel_tasks"] == 2


def test_scheduler_serializes_parallel_tasks_when_agent_capacity_is_one(db_session):
    goal = _goal(db_session, max_parallel_tasks=2)
    agent = AgentStation(id=str(uuid.uuid4()), name="Solo", role="coder", default_model_id="m", max_concurrency=1)
    db_session.add(agent); db_session.commit()
    tasks = [_task(db_session, goal, f"Parallel {index}", parallel=True) for index in range(2)]
    for task in tasks:
        task.assigned_agent_id = agent.id
    db_session.commit()

    decision = scheduler_service.schedule_ready_tasks(db_session, goal)
    assert len(decision.selected_tasks) == 1
    assert db_session.query(ExecutionLog).filter(ExecutionLog.event_type == "task.parallel_group_started").count() == 0


def test_waiting_approval_can_be_approved_and_scheduled(db_session):
    goal = _goal(db_session)
    task = _task(db_session, goal, "Approve me", status="waiting_approval")
    waiting = scheduler_service.schedule_ready_tasks(db_session, goal)
    assert waiting.goal_status == "waiting_approval"
    assert waiting.selected_tasks == []

    approved = task_service.approve_task(db_session, task.id)
    assert approved["status"] == "pending"
    ready = scheduler_service.schedule_ready_tasks(db_session, goal)
    assert [item.id for item in ready.selected_tasks] == [task.id]


def test_skipped_dependency_allows_downstream_task_to_run(db_session):
    goal = _goal(db_session)
    optional = _task(db_session, goal, "Optional")
    downstream = _task(db_session, goal, "Downstream", [optional.id])
    skipped = task_service.skip_task(db_session, optional.id, "Not needed in revised scope")
    decision = scheduler_service.schedule_ready_tasks(db_session, goal)

    assert skipped["status"] == "skipped"
    assert [item.id for item in decision.selected_tasks] == [downstream.id]


def test_scheduler_reports_no_ready_task_instead_of_claiming_completion(db_session):
    goal = _goal(db_session)
    decision = scheduler_service.schedule_ready_tasks(db_session, goal)
    assert decision.goal_status == "blocked"
    assert decision.blocked_reason == "Goal has no executable tasks"
