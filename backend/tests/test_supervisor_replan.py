import uuid

from src.models.agent import AgentStation
from src.models.workspace import Goal, Task
from src.services import review_service


def test_supervisor_materializes_unverified_code_as_replan(db_session):
    agent = AgentStation(id=str(uuid.uuid4()), name="Reviewer", role="reviewer", default_model_id="missing-model", is_enabled=True)
    goal = Goal(id=str(uuid.uuid4()), title="Repair API", status="completed")
    original = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Build API", description="Fix endpoint", status="completed_unverified", assigned_agent_id=agent.id, task_type="coding")
    original.set_json("acceptance_criteria", [{"type": "tests_pass"}])
    db_session.add_all([agent, goal, original])
    db_session.commit()

    review_service.generate_review(db_session, goal.id, "run-test")

    children = db_session.query(Task).filter(Task.parent_task_id == original.id).all()
    db_session.refresh(goal)
    assert len(children) == 1
    assert children[0].status == "pending"
    assert children[0].title == "Replan: Build API"
    assert goal.status == "running"
