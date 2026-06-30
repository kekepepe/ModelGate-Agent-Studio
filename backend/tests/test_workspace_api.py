import pytest
from fastapi.testclient import TestClient


class TestCreateGoal:
    def test_create_goal_success(self, client: TestClient):
        resp = client.post("/api/v1/goals", json={
            "title": "实现用户认证系统",
            "description": "需要支持邮箱和手机号登录",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert "goal_id" in data["data"]
        assert data["data"]["status"] == "idle"

    def test_create_goal_empty_title(self, client: TestClient):
        resp = client.post("/api/v1/goals", json={"title": ""})
        assert resp.status_code == 422

    def test_create_goal_minimal(self, client: TestClient):
        resp = client.post("/api/v1/goals", json={"title": "测试"})
        assert resp.status_code == 201
        assert resp.json()["data"]["status"] == "idle"


class TestStartGoal:
    def test_start_goal_success(self, client: TestClient, db_session):
        # Create agents first (need at least a planner)
        from src.models.agent import AgentStation
        import uuid
        planner = AgentStation(
            id=str(uuid.uuid4()),
            name="Planner",
            role="planner",
            default_model_id="model-gpt-4-turbo",
            status="idle",
            is_enabled=True,
        )
        db_session.add(planner)
        db_session.commit()

        # Create goal
        resp = client.post("/api/v1/goals", json={"title": "测试目标"})
        goal_id = resp.json()["data"]["goal_id"]

        resp2 = client.post(f"/api/v1/goals/{goal_id}/start")
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["success"] is True
        assert data["data"]["status"] == "planning"

    def test_start_goal_not_found(self, client: TestClient):
        resp = client.post("/api/v1/goals/nonexistent/start")
        assert resp.status_code == 404

    def test_start_goal_already_running(self, client: TestClient, db_session):
        import uuid
        from src.models.agent import AgentStation
        planner = AgentStation(
            id=str(uuid.uuid4()), name="Planner", role="planner",
            default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True,
        )
        db_session.add(planner)
        db_session.commit()

        resp = client.post("/api/v1/goals", json={"title": "测试目标"})
        goal_id = resp.json()["data"]["goal_id"]
        client.post(f"/api/v1/goals/{goal_id}/start")
        # Try starting again
        resp2 = client.post(f"/api/v1/goals/{goal_id}/start")
        assert resp2.status_code == 400


class TestGetTask:
    def test_get_task_success(self, client: TestClient, db_session):
        import uuid
        from src.models.agent import AgentStation
        from src.models.workspace import Goal, Task

        planner = AgentStation(
            id=str(uuid.uuid4()), name="Planner", role="planner",
            default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True,
        )
        db_session.add(planner)
        db_session.commit()

        goal = Goal(id=str(uuid.uuid4()), title="Test", status="idle")
        db_session.add(goal)
        db_session.commit()

        task = Task(
            id=str(uuid.uuid4()), goal_id=goal.id, title="Plan task",
            status="pending", assigned_agent_id=planner.id,
        )
        db_session.add(task)
        db_session.commit()

        resp = client.get(f"/api/v1/tasks/{task.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == task.id
        assert data["title"] == "Plan task"
        assert data["agent_name"] == "Planner"

    def test_get_task_not_found(self, client: TestClient):
        resp = client.get("/api/v1/tasks/nonexistent")
        assert resp.status_code == 404


class TestWorkspaceState:
    def test_workspace_state_success(self, client: TestClient, db_session):
        import uuid
        from src.models.agent import AgentStation
        from src.models.workspace import Goal, Task

        agent = AgentStation(
            id=str(uuid.uuid4()), name="Coder", role="coder",
            default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True,
        )
        db_session.add(agent)
        db_session.commit()

        goal = Goal(id=str(uuid.uuid4()), title="Workspace Test", status="running")
        db_session.add(goal)
        db_session.commit()

        task1 = Task(
            id=str(uuid.uuid4()), goal_id=goal.id, title="Task 1",
            status="running", assigned_agent_id=agent.id,
        )
        task2 = Task(
            id=str(uuid.uuid4()), goal_id=goal.id, title="Task 2",
            status="pending",
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        resp = client.get(f"/api/v1/workspace/{goal.id}/state")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["goal"]["id"] == goal.id
        assert data["goal"]["status"] == "running"
        assert len(data["tasks"]) == 2
        assert len(data["agents"]) >= 1
        assert "workers" in data

    def test_workspace_state_not_found(self, client: TestClient):
        resp = client.get("/api/v1/workspace/nonexistent/state")
        assert resp.status_code == 404
