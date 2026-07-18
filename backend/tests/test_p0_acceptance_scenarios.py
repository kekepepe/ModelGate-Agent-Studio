"""The six P0 product scenarios, kept together as an executable exit gate."""

import uuid

from src.models.agent import AgentStation
from src.models.workspace import ExecutionPlan, Goal, PlanChange
from src.schemas.planning import ExecutionPlanContract, PlanTaskContract, ReplanRequest
from src.services import planning_service, replan_service
from src.services.orchestrator_service import RuleBasedPlanningFallback, _materialize_plan


def _seed_capabilities(db_session):
    agents = {}
    for role in ("planner", "coder", "reviewer", "research", "summarizer"):
        agent = AgentStation(
            id=str(uuid.uuid4()),
            name=role.title(),
            role=role,
            default_model_id=f"{role}-model",
            is_enabled=True,
        )
        agents[role] = agent
    db_session.add_all(agents.values())
    db_session.commit()
    return agents


def _fallback_plan(db_session, title):
    goal = Goal(id=str(uuid.uuid4()), title=title, status="planning", execution_mode="mock")
    db_session.add(goal)
    db_session.commit()
    plan, assignments = RuleBasedPlanningFallback().build(db_session, goal)
    return goal, plan, assignments


def test_p0_scenario_1_explain_function_uses_direct_without_planner_or_reviewer(db_session):
    _seed_capabilities(db_session)
    _, plan, assignments = _fallback_plan(db_session, "解释这个函数做什么")

    assert plan.task_mode == "direct"
    assert [task.task_type for task in plan.tasks] == ["direct"]
    assert [agent.role for agent in assignments.values()] == ["summarizer"]


def test_p0_scenario_2_readme_sentence_uses_one_writer_with_minimum_contract(db_session):
    _seed_capabilities(db_session)
    _, plan, assignments = _fallback_plan(db_session, "修改 README 中的一句话")

    assert plan.task_mode == "single_agent"
    assert [task.task_type for task in plan.tasks] == ["coding"]
    assert plan.tasks[0].acceptance_criteria == [{"type": "diff_exists"}]
    assert [agent.role for agent in assignments.values()] == ["coder"]


def test_p0_scenario_3_login_bug_routes_coder_then_verifier_and_can_revise(db_session):
    _seed_capabilities(db_session)
    _, plan, _ = _fallback_plan(db_session, "修复登录 Bug 并运行测试")

    assert plan.task_mode == "sequential_multi_agent"
    assert [task.task_type for task in plan.tasks] == ["coding", "verification"]
    assert plan.tasks[1].dependencies == [plan.tasks[0].client_task_id]
    assert {item["type"] for item in plan.tasks[0].acceptance_criteria} == {"diff_exists", "tests_pass"}


def test_p0_scenario_4_research_then_code_preserves_all_three_stages(db_session):
    _seed_capabilities(db_session)
    _, plan, _ = _fallback_plan(db_session, "先调研方案再修改代码")

    assert plan.task_mode == "sequential_multi_agent"
    assert [task.task_type for task in plan.tasks] == ["research", "coding", "verification"]
    assert plan.tasks[1].dependencies == [plan.tasks[0].client_task_id]
    assert plan.tasks[2].dependencies == [plan.tasks[1].client_task_id]


def test_p0_scenario_5_frontend_backend_use_isolated_parallel_merge_then_verify(db_session):
    _seed_capabilities(db_session)
    _, plan, _ = _fallback_plan(db_session, "前后端分别实现接口和页面")

    assert plan.task_mode == "parallel_multi_agent"
    assert [task.task_type for task in plan.tasks] == [
        "planning", "coding", "coding", "merge", "verification",
    ]
    frontend, backend = plan.tasks[1:3]
    merge, verifier = plan.tasks[3:5]
    assert frontend.parallel_safe and backend.parallel_safe
    assert {frontend.workspace_scope, backend.workspace_scope} == {"frontend/**", "backend/**"}
    assert set(merge.dependencies) == {frontend.client_task_id, backend.client_task_id}
    assert verifier.dependencies == [merge.client_task_id]


def test_p0_scenario_6_reviewer_architecture_issue_creates_new_plan_version(db_session):
    agents = _seed_capabilities(db_session)
    goal = Goal(id=str(uuid.uuid4()), title="Architecture review", status="running", execution_mode="mock")
    db_session.add(goal)
    db_session.commit()
    contract = ExecutionPlanContract(
        task_mode="sequential_multi_agent",
        goal_summary="Build and independently review an architecture change",
        activation_reason="Architecture risk requires an independent review.",
        tasks=[
            PlanTaskContract(
                client_task_id="build",
                objective="Build architecture change",
                task_type="coding",
                required_capabilities=["code_edit"],
                acceptance_criteria=[{"type": "diff_exists"}],
            ),
            PlanTaskContract(
                client_task_id="review",
                objective="Review architecture",
                task_type="verification",
                required_capabilities=["review"],
                dependencies=["build"],
                acceptance_criteria=[{"type": "diff_exists"}],
            ),
        ],
    )
    first = planning_service.persist_plan(db_session, goal, contract, planner_type="model")
    runtime_tasks = _materialize_plan(
        db_session,
        goal,
        first,
        {"build": agents["coder"], "review": agents["reviewer"]},
    )
    planning_service.activate_plan(db_session, first)
    build = next(task for task in runtime_tasks if task.task_type == "coding")
    build.status = "revision_required"
    build.verification_status = "failed"
    db_session.commit()

    result = replan_service.request_replan(db_session, goal.id, ReplanRequest(
        trigger="supervisor_review",
        reason="Reviewer found an architecture boundary violation.",
        evidence=[{"finding": "architecture boundary violation"}],
        replace_task_ids=[build.id],
    ))

    versions = db_session.query(ExecutionPlan).filter(
        ExecutionPlan.goal_id == goal.id
    ).order_by(ExecutionPlan.version).all()
    change = db_session.query(PlanChange).filter(
        PlanChange.to_plan_version_id == versions[1].id
    ).one()
    assert [plan.version for plan in versions] == [1, 2]
    assert versions[0].status == "superseded" and versions[1].status == "active"
    assert result["change"]["replaced_task_ids"] == ["build"]
    assert change._get_json("evidence")[1]["finding"] == "architecture boundary violation"
