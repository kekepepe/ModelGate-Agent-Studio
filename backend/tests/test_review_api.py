import uuid
from fastapi.testclient import TestClient


def _seed_review_data(db_session):
    from src.models.agent import AgentStation
    from src.models.model import Model
    from src.models.workspace import Goal, Task

    planner = AgentStation(
        id=str(uuid.uuid4()), name="Planner", role="planner",
        default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True,
        system_prompt="Plan carefully.",
    )
    supervisor = AgentStation(
        id=str(uuid.uuid4()), name="Supervisor", role="supervisor",
        default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True,
        system_prompt="Review outputs.",
    )
    db_session.add_all([planner, supervisor])

    m1 = Model(id="model-gpt-4-turbo", provider="openai", model_name="gpt-4-turbo",
               display_name="GPT-4 Turbo", is_enabled=True, max_context_tokens=128000, cost_level=4, speed_level=3)
    m1.set_capability_tags(["reasoning"])
    db_session.add(m1)
    db_session.commit()

    goal = Goal(id=str(uuid.uuid4()), title="Test Goal", status="completed")
    db_session.add(goal)
    db_session.commit()

    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Done task",
        description="Task done", status="completed",
        assigned_agent_id=planner.id, output="Task output: completed successfully.",
        tokens_used=300,
    )
    db_session.add(task)
    db_session.commit()
    return goal


class TestReviewAPI:
    def test_generate_review_success(self, client: TestClient, db_session):
        goal = _seed_review_data(db_session)
        resp = client.post(f"/api/v1/runtime/review/{goal.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["goal_id"] == goal.id
        assert data["status"] == "completed"
        assert "passed" in data
        assert isinstance(data["issues"], list)

    def test_get_review_after_generate(self, client: TestClient, db_session):
        goal = _seed_review_data(db_session)
        client.post(f"/api/v1/runtime/review/{goal.id}")
        resp = client.get(f"/api/v1/runtime/review/{goal.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["goal_id"] == goal.id
        assert "summary" in data

    def test_generate_review_goal_not_found(self, client: TestClient):
        resp = client.post("/api/v1/runtime/review/nonexistent")
        assert resp.status_code == 400

    def test_get_review_no_review_exists(self, client: TestClient):
        resp = client.get("/api/v1/runtime/review/nonexistent")
        assert resp.status_code == 404
