import uuid

from src.models.agent import AgentStation
from src.models.workspace import ExecutionPlan, Goal, PlanChange, Task
from src.services import review_service


def test_supervisor_materializes_unverified_code_as_replan(db_session):
    reviewer = AgentStation(id=str(uuid.uuid4()), name="Reviewer", role="reviewer", default_model_id="missing-model", is_enabled=True)
    coder = AgentStation(id=str(uuid.uuid4()), name="Coder", role="coder", default_model_id="missing-model", is_enabled=True)
    goal = Goal(id=str(uuid.uuid4()), title="Repair API", status="completed")
    original = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Build API", description="Fix endpoint", status="completed_unverified", assigned_agent_id=reviewer.id, task_type="coding")
    original.set_json("acceptance_criteria", [{"type": "tests_pass"}])
    db_session.add_all([reviewer, coder, goal, original])
    db_session.commit()

    review_service.generate_review(db_session, goal.id, "run-test")

    children = db_session.query(Task).filter(Task.parent_task_id == original.id).all()
    db_session.refresh(goal)
    assert len(children) == 1
    assert children[0].status == "pending"
    assert children[0].title == "Revise: Build API"
    assert children[0].assigned_agent_id == coder.id
    assert goal.status == "running"
    plans = db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal.id).order_by(ExecutionPlan.version).all()
    assert [plan.version for plan in plans] == [1, 2]
    assert plans[0].status == "superseded"
    assert plans[1].status == "active"
    change = db_session.query(PlanChange).filter(PlanChange.to_plan_version_id == plans[1].id).one()
    assert change.change_type == "replan"
    assert change._get_json("replaced_task_ids") == ["legacy-1"]
