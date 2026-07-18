import json
import uuid

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.model import Model
from src.models.workspace import ExecutionPlan, Goal
from src.services.orchestrator_service import plan_goal
from src.services.providers.mock_provider import MockModelProvider
from src.services.providers.provider_factory import create_provider, set_provider


def _seed_planning_team(db_session):
    model = Model(
        id="planner-json-model",
        provider="mock",
        model_name="planner-json-model",
        display_name="Planner JSON",
        is_enabled=True,
    )
    model.set_capability_tags(["reasoning", "planning"])
    planner = AgentStation(
        id=str(uuid.uuid4()),
        name="Planner",
        role="planner",
        default_model_id=model.id,
        is_enabled=True,
    )
    researcher = AgentStation(
        id=str(uuid.uuid4()),
        name="Researcher",
        role="research",
        default_model_id=model.id,
        is_enabled=True,
    )
    researcher.set_allowed_tools(["file_read"])
    db_session.add_all([model, planner, researcher])
    db_session.commit()
    return planner, researcher


def _valid_research_plan():
    return {
        "task_mode": "single_agent",
        "goal_summary": "Research the current architecture",
        "assumptions": [],
        "required_context": ["architecture docs"],
        "activation_reason": "One research capability is sufficient.",
        "tasks": [{
            "client_task_id": "research-architecture",
            "objective": "Research the current architecture",
            "task_type": "research",
            "required_capabilities": ["research"],
            "required_tools": ["file_read"],
            "dependencies": [],
            "acceptance_criteria": [],
            "risk_level": "low",
            "parallel_safe": False,
            "context_query": "architecture",
            "approval_required": False,
        }],
        "final_acceptance_criteria": [],
        "human_approval_points": [],
        "estimated_cost": {"token_upper_bound": 4000},
        "fallback_reason": None,
    }


def test_model_orchestrator_repairs_invalid_json_then_persists_model_plan(db_session):
    _, researcher = _seed_planning_team(db_session)
    outputs = iter(["not-json", json.dumps(_valid_research_plan())])
    provider = MockModelProvider(default_latency_ms=0)
    provider.configure_model(
        "planner-json-model",
        output_text_fn=lambda _prompt, _system: next(outputs),
        latency_ms=0,
    )
    set_provider(provider)
    try:
        goal = Goal(
            id=str(uuid.uuid4()),
            title="调研当前架构",
            status="planning",
            execution_mode="mock",
        )
        db_session.add(goal)
        db_session.commit()
        tasks = plan_goal(db_session, goal)
    finally:
        set_provider(create_provider("mock"))

    plan = db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal.id).one()
    assert plan.planner_type == "model"
    assert plan.task_mode == "single_agent"
    assert len(plan._get_json("repair_records", [])) == 1
    assert "not-json" in plan._get_json("repair_records", [])[0]["raw_output"]
    assert len(tasks) == 1
    assert tasks[0].assigned_agent_id == researcher.id
    assert tasks[0].plan_source == "model"
    assert tasks[0].title == "Research the current architecture"


def test_invalid_model_plan_falls_back_visibly_with_repair_history(db_session):
    planner, _ = _seed_planning_team(db_session)
    provider = MockModelProvider(default_latency_ms=0)
    provider.configure_model("planner-json-model", output_text="still not JSON", latency_ms=0)
    set_provider(provider)
    try:
        goal = Goal(
            id=str(uuid.uuid4()),
            title="简单解释",
            status="planning",
            execution_mode="mock",
        )
        db_session.add(goal)
        db_session.commit()
        tasks = plan_goal(db_session, goal)
    finally:
        set_provider(create_provider("mock"))

    plan = db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal.id).one()
    fallback_event = db_session.query(ExecutionLog).filter(
        ExecutionLog.goal_id == goal.id,
        ExecutionLog.event_type == "plan.fallback_used",
    ).one()
    assert plan.planner_type == "rule_fallback"
    assert "ModelPlanningFailed" in plan.fallback_reason
    assert len(plan._get_json("repair_records", [])) == 3
    assert fallback_event.event_status == "completed"
    assert len(tasks) == 1
    assert tasks[0].assigned_agent_id == planner.id
    assert tasks[0].plan_source == "rule_fallback"
