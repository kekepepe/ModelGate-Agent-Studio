import uuid

import pytest
from pydantic import ValidationError

from src.models.agent import AgentStation
from src.models.workspace import ExecutionPlan, Goal, PlanChange, PlanTask, Task
from src.schemas.planning import ExecutionPlanContract
from src.services import plan_policy_service, planning_service


def _task(task_id, **overrides):
    payload = {
        "client_task_id": task_id,
        "objective": f"Objective {task_id}",
        "task_type": "research",
        "required_capabilities": ["research"],
        "required_tools": ["file_read"],
        "dependencies": [],
        "acceptance_criteria": [],
        "risk_level": "low",
        "parallel_safe": False,
    }
    payload.update(overrides)
    return payload


def _plan(tasks, **overrides):
    payload = {
        "task_mode": "sequential_multi_agent" if len(tasks) > 1 else "single_agent",
        "goal_summary": "Deliver a validated change",
        "activation_reason": "The requested capabilities have dependent work.",
        "tasks": tasks,
    }
    payload.update(overrides)
    return payload


def test_direct_plan_allows_zero_or_one_task():
    empty = ExecutionPlanContract.model_validate(_plan([], task_mode="direct"))
    one = ExecutionPlanContract.model_validate(_plan([_task("answer", task_type="direct")], task_mode="direct"))
    assert empty.tasks == []
    assert one.tasks[0].client_task_id == "answer"


@pytest.mark.parametrize(
    "tasks, message",
    [
        ([_task("same"), _task("same")], "Task IDs must be unique"),
        ([_task("one", dependencies=["missing"])], "dependencies that do not exist"),
        ([_task("one", dependencies=["two"]), _task("two", dependencies=["one"])], "contains a cycle"),
    ],
)
def test_plan_rejects_invalid_dag(tasks, message):
    with pytest.raises(ValidationError, match=message):
        ExecutionPlanContract.model_validate(_plan(tasks))


def test_plan_rejects_workspace_write_without_completion_contract():
    with pytest.raises(ValidationError, match="requires at least one acceptance criterion"):
        ExecutionPlanContract.model_validate(_plan([
            _task(
                "write",
                task_type="coding",
                required_capabilities=["code_edit"],
                required_tools=["file_write"],
            )
        ]))


def test_parallel_plan_rejects_overlapping_write_scopes_without_merge_strategy():
    tasks = [
        _task(
            "frontend-a",
            task_type="coding",
            required_tools=["file_patch"],
            acceptance_criteria=[{"type": "diff_exists"}],
            parallel_safe=True,
            workspace_scope="frontend/src/**",
        ),
        _task(
            "frontend-b",
            task_type="coding",
            required_tools=["file_patch"],
            acceptance_criteria=[{"type": "diff_exists"}],
            parallel_safe=True,
            workspace_scope="frontend/**",
        ),
    ]
    with pytest.raises(ValidationError, match="overlapping scopes"):
        ExecutionPlanContract.model_validate(_plan(tasks, task_mode="parallel_multi_agent"))


def test_parallel_preflight_records_scopes_isolation_merge_order_and_coordination_cost():
    contract = ExecutionPlanContract.model_validate(_plan([
        _task("frontend", task_type="coding", required_capabilities=["code_edit"], required_tools=["file_patch"], acceptance_criteria=[{"type": "diff_exists"}], parallel_safe=True, workspace_scope="frontend/**"),
        _task("backend", task_type="coding", required_capabilities=["code_edit"], required_tools=["file_patch"], acceptance_criteria=[{"type": "diff_exists"}], parallel_safe=True, workspace_scope="backend/**"),
        _task("merge", task_type="merge", required_capabilities=["code_edit"], required_tools=["file_patch"], acceptance_criteria=[{"type": "diff_exists"}], dependencies=["frontend", "backend"]),
        _task("verify", task_type="verification", required_capabilities=["review"], dependencies=["merge"]),
    ], task_mode="parallel_multi_agent"))
    analysis = plan_policy_service.analyze(contract)
    assert analysis["parallel_writer_task_ids"] == ["frontend", "backend"]
    assert analysis["conflict_preflight"] == []
    assert analysis["isolation_required"] is True
    assert analysis["deterministic_merge_order"] == ["frontend", "backend"]
    assert analysis["coordination_task_ids"] == ["merge", "verify"]
    assert analysis["estimated_coordination_token_upper_bound"] == 2000


def test_high_risk_task_requires_approval_or_downstream_reviewer():
    high_risk = _task("migrate", risk_level="high")
    with pytest.raises(ValidationError, match="requires a human approval point or downstream Reviewer"):
        ExecutionPlanContract.model_validate(_plan([high_risk]))

    reviewed = ExecutionPlanContract.model_validate(_plan([
        high_risk,
        _task("review", task_type="verification", dependencies=["migrate"]),
    ]))
    assert reviewed.tasks[-1].task_type == "verification"


def test_started_goal_persists_active_plan_and_runtime_provenance(client, db_session):
    agents = [
        AgentStation(
            id=str(uuid.uuid4()),
            name=role.title(),
            role=role,
            default_model_id=f"{role}-model",
            is_enabled=True,
        )
        for role in ("planner", "coder", "reviewer")
    ]
    db_session.add_all(agents)
    db_session.commit()

    goal_id = client.post("/api/v1/goals", json={
        "title": "修复登录 Bug 并运行测试",
        "execution_mode": "mock",
    }).json()["data"]["goal_id"]
    response = client.post(f"/api/v1/goals/{goal_id}/start")
    assert response.status_code == 200, response.text

    plan = db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal_id).one()
    assert plan._get_json("estimated_cost", {})["multi_agent_analysis"]["policy"] == "smallest_safe_team_v1"
    plan_tasks = db_session.query(PlanTask).filter(PlanTask.plan_version_id == plan.id).all()
    runtime_tasks = db_session.query(Task).filter(Task.goal_id == goal_id).all()
    change = db_session.query(PlanChange).filter(PlanChange.to_plan_version_id == plan.id).one()

    assert plan.status == "active"
    assert plan.confirmed_at is None
    assert plan.version == 1
    assert plan.task_mode == "sequential_multi_agent"
    assert plan.planner_type == "rule_fallback"
    assert plan.fallback_reason
    assert len(plan_tasks) == len(runtime_tasks) == 2
    assert {item.runtime_task_id for item in plan_tasks} == {item.id for item in runtime_tasks}
    assert all(item.plan_version_id == plan.id and item.plan_source == "rule_fallback" for item in runtime_tasks)
    assert change.change_type == "created"

    api_plan = client.get(f"/api/v1/goals/{goal_id}/plans/1")
    assert api_plan.status_code == 200
    payload = api_plan.json()["data"]
    assert payload["plan_id"] == plan.plan_id
    assert payload["task_mode"] == "sequential_multi_agent"
    assert len(payload["tasks"]) == 2

    confirmed = client.post(f"/api/v1/goals/{goal_id}/plans/1/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["confirmed_at"]


def test_persist_plan_creates_new_version_without_overwriting_history(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Versioned plan", status="planning")
    db_session.add(goal)
    db_session.commit()
    first_payload = ExecutionPlanContract.model_validate(_plan([_task("research")]))
    first = planning_service.persist_plan(db_session, goal, first_payload, planner_type="model")
    second_payload = ExecutionPlanContract.model_validate(_plan([_task("research-v2")]))
    second = planning_service.persist_plan(db_session, goal, second_payload, planner_type="model")

    db_session.refresh(first)
    assert first.plan_id == second.plan_id
    assert first.version == 1 and first.status == "superseded"
    assert second.version == 2 and second.status == "validated"
    assert db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal.id).count() == 2
