import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.models.workspace import Goal


def _seed_runtime_data(db_session):
    """Create agents, models, goal, and tasks needed for runtime tests."""
    from src.models.agent import AgentStation
    from src.models.model import Model
    from src.models.workspace import Goal, Task

    planner = AgentStation(
        id=str(uuid.uuid4()), name="Planner", role="planner",
        default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True,
        system_prompt="Plan carefully.",
    )
    coder = AgentStation(
        id=str(uuid.uuid4()), name="Coder", role="coder",
        default_model_id="model-claude-opus", status="idle", is_enabled=True,
        system_prompt="Write code.",
    )
    db_session.add_all([planner, coder])

    models = [
        Model(id="model-gpt-4-turbo", provider="openai", model_name="gpt-4-turbo",
              display_name="GPT-4 Turbo", is_enabled=True, max_context_tokens=128000,
              cost_level=4, speed_level=3),
        Model(id="model-claude-opus", provider="anthropic", model_name="claude-3-opus",
              display_name="Claude 3 Opus", is_enabled=True, max_context_tokens=200000,
              cost_level=5, speed_level=3),
    ]
    for m in models:
        m.set_capability_tags(["code", "reasoning"])
        db_session.add(m)
    db_session.commit()

    goal = Goal(id=str(uuid.uuid4()), title="API Test Goal", status="planning")
    db_session.add(goal)
    db_session.commit()

    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Plan task",
        description="Plan the work", status="pending",
        assigned_agent_id=planner.id,
    )
    task2 = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Code task",
        description="Write code", status="pending",
        assigned_agent_id=coder.id,
    )
    db_session.add_all([task, task2])
    db_session.commit()
    return goal, task


class TestExecuteGoalAPI:
    def test_execute_goal_success(self, client: TestClient, db_session):
        goal, _ = _seed_runtime_data(db_session)
        resp = client.post(f"/api/v1/runtime/execute/{goal.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["goal_id"] == goal.id
        assert data["status"] in ("completed", "in_progress")
        assert data["total_tokens_used"] > 0
        assert len(data["execution_log"]) >= 1

    def test_execute_goal_not_found(self, client: TestClient):
        resp = client.post("/api/v1/runtime/execute/nonexistent")
        assert resp.status_code == 404

    def test_execute_goal_wrong_state(self, client: TestClient, db_session):
        from src.models.workspace import Goal
        goal = Goal(id=str(uuid.uuid4()), title="Idle", status="idle")
        db_session.add(goal)
        db_session.commit()
        resp = client.post(f"/api/v1/runtime/execute/{goal.id}")
        assert resp.status_code == 400

    def test_start_goal_returns_immediately_and_queues_worker(self, client: TestClient, db_session):
        goal, _ = _seed_runtime_data(db_session)
        with patch("src.routes.runtime.threading.Thread") as thread:
            resp = client.post(f"/api/v1/runtime/start/{goal.id}")
        assert resp.status_code == 202
        assert resp.json()["data"] == {"goal_id": goal.id, "status": "running"}
        thread.return_value.start.assert_called_once()

    def test_resume_queues_a_new_background_worker(self, client: TestClient, db_session):
        from src.models.workspace import RuntimeRun
        goal = Goal(id=str(uuid.uuid4()), title="Paused", status="paused", execution_mode="mock")
        run = RuntimeRun(id=str(uuid.uuid4()), goal_id=goal.id, execution_mode="mock", status="paused")
        goal.run_id = run.id
        db_session.add_all([goal, run])
        db_session.commit()
        with patch("src.routes.runtime.threading.Thread") as thread:
            resp = client.post(f"/api/v1/runtime/resume/{goal.id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "running"
        thread.return_value.start.assert_called_once()


class TestExecuteStepAPI:
    def test_execute_step_success(self, client: TestClient, db_session):
        _, task = _seed_runtime_data(db_session)
        resp = client.post(f"/api/v1/runtime/execute-step/{task.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["task_id"] == task.id
        assert data["status"] == "completed"
        assert data["output"] is not None
        assert data["tokens_used"] > 0

    def test_execute_step_not_found(self, client: TestClient):
        resp = client.post("/api/v1/runtime/execute-step/nonexistent")
        assert resp.status_code == 400


class TestRuntimeStatusAPI:
    def test_verified_task_is_not_reported_as_incomplete_risk(self, db_session):
        from src.models.workspace import Task
        from src.services.runtime_service import _build_final_summary
        goal = Goal(id=str(uuid.uuid4()), title="Verified", status="completed")
        task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Checked fix", status="completed_verified")
        db_session.add_all([goal, task])
        db_session.commit()
        summary = _build_final_summary(db_session, goal, [task], handoff_count=0)
        assert summary["completed"] == ["Checked fix"]
        assert summary["incomplete"] == []
        assert not any("未完成" in risk for risk in summary["risks"])

    def test_status_after_execute(self, client: TestClient, db_session):
        goal, _ = _seed_runtime_data(db_session)
        # Execute first to generate data
        client.post(f"/api/v1/runtime/execute/{goal.id}")
        # Now check status
        resp = client.get(f"/api/v1/runtime/status/{goal.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["goal_id"] == goal.id
        assert data["goal_title"] == "API Test Goal"
        assert data["goal_status"] in ("completed", "running", "planning")
        assert data["total_tasks"] >= 1
        assert data["completed_tasks"] >= 1
        assert data["log_count"] > 0
        assert data["model_call_count"] > 0
        assert data["final_summary"]["completed"]
        assert data["final_summary"]["quality"]["status"] in ("completed", "not_available")
        assert data["final_summary"]["cost"]["available"] is False

    def test_status_goal_not_found(self, client: TestClient):
        resp = client.get("/api/v1/runtime/status/nonexistent")
        assert resp.status_code == 404

    def test_status_no_execution_yet(self, client: TestClient, db_session):
        from src.models.workspace import Goal
        goal = Goal(id=str(uuid.uuid4()), title="Fresh Goal", status="planning")
        db_session.add(goal)
        db_session.commit()
        resp = client.get(f"/api/v1/runtime/status/{goal.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_tasks"] == 0
        assert data["completed_tasks"] == 0
        assert data["log_count"] == 0


class TestRuntimeEventsAPI:
    def test_completed_goal_exposes_persisted_events_as_sse(self, client: TestClient, db_session):
        goal, _ = _seed_runtime_data(db_session)
        client.post(f"/api/v1/runtime/execute/{goal.id}")
        response = client.get(f"/api/v1/runtime/events/{goal.id}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "event: runtime" in response.text
        assert "model_call" in response.text
        assert "event: end" in response.text

    def test_events_goal_not_found(self, client: TestClient):
        response = client.get("/api/v1/runtime/events/nonexistent")
        assert response.status_code == 404
