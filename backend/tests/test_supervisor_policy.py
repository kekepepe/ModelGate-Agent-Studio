import uuid

from src.models.handoff import ExecutionLog, HandoffRecord
from src.models.workspace import ExecutionPlan, Goal, Task
from src.services.supervisor_policy_service import evaluate


def _goal_plan(db_session, mode="single_agent"):
    goal = Goal(id=str(uuid.uuid4()), title="Fix one file", status="running")
    plan = ExecutionPlan(
        id=str(uuid.uuid4()), plan_id=str(uuid.uuid4()), goal_id=goal.id, version=1,
        status="active", task_mode=mode, goal_summary=goal.title,
        activation_reason="Smallest safe path", planner_type="rule_fallback",
    )
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Edit", status="completed_verified", task_type="coding")
    task.set_json("acceptance_criteria", [{"type": "diff_exists"}, {"type": "tests_pass"}])
    db_session.add_all([goal, plan, task]); db_session.commit()
    return goal, task


def test_simple_deterministic_goal_skips_supervisor(db_session):
    goal, task = _goal_plan(db_session)
    result = evaluate(db_session, goal, [task])
    assert result["activate"] is False
    assert "deterministic verification" in result["reasons"][0]


def test_high_risk_parallel_or_subjective_work_activates_supervisor(db_session):
    goal, task = _goal_plan(db_session, "parallel_multi_agent")
    task.risk_level = "high"
    task.set_json("acceptance_criteria", [{"type": "editorial_quality"}])
    db_session.commit()
    result = evaluate(db_session, goal, [task])
    assert result["activate"] is True
    assert any("high-risk" in reason for reason in result["reasons"])
    assert any("Parallel" in reason for reason in result["reasons"])
    assert any("editorial_quality" in reason for reason in result["reasons"])


def test_handoff_or_replan_activates_supervisor(db_session):
    goal, task = _goal_plan(db_session)
    db_session.add(HandoffRecord(
        id=str(uuid.uuid4()), goal_id=goal.id, task_id=task.id, from_agent_id="a1",
        from_model_id="m1", to_agent_id="a2", to_model_id="m2",
        reason="manual", reason_description="Need another capability",
        status="pending",
    ))
    db_session.add(ExecutionLog(
        id=str(uuid.uuid4()), goal_id=goal.id, event_type="plan.replanned", event_status="completed",
    ))
    db_session.commit()
    result = evaluate(db_session, goal, [task])
    assert result["activate"] is True
    assert any("Handoff" in reason for reason in result["reasons"])
    assert any("Replan" in reason for reason in result["reasons"])
