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

    def test_create_goal_accepts_team_preset(self, client: TestClient, db_session):
        from src.models.workspace import Goal

        response = client.post("/api/v1/goals", json={"title": "Ship feature", "team_preset": "code-delivery"})
        assert response.status_code == 201
        goal = db_session.query(Goal).filter(Goal.id == response.json()["data"]["goal_id"]).one()
        assert goal.team_preset == "code-delivery"


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
        from src.models.handoff import ExecutionLog
        event_types = {
            event.event_type
            for event in db_session.query(ExecutionLog).filter(ExecutionLog.goal_id == goal_id).all()
        }
        assert {"plan.generating", "plan.created"}.issubset(event_types)

    def test_start_goal_activates_only_needed_serial_capabilities(self, client: TestClient, db_session):
        """A routine code Goal does not create a redundant Planner Task."""
        from src.models.agent import AgentStation
        from src.models.workspace import Task
        import uuid

        agents = [
            AgentStation(id=str(uuid.uuid4()), name="Planner", role="planner", default_model_id="model-gpt-4-turbo", is_enabled=True),
            AgentStation(id=str(uuid.uuid4()), name="Coder", role="coder", default_model_id="model-deepseek-coder", is_enabled=True),
            AgentStation(id=str(uuid.uuid4()), name="Reviewer", role="reviewer", default_model_id="model-claude-3-haiku", is_enabled=True),
        ]
        db_session.add_all(agents)
        db_session.commit()

        goal_id = client.post("/api/v1/goals", json={"title": "交付登录模块"}).json()["data"]["goal_id"]
        response = client.post(f"/api/v1/goals/{goal_id}/start")
        assert response.status_code == 200

        tasks = db_session.query(Task).filter(Task.goal_id == goal_id).order_by(Task.priority.desc()).all()
        assert [task.title.split(":", 1)[0] for task in tasks] == ["Build", "Verify"]
        assert [task.assigned_agent_id for task in tasks] == [agents[1].id, agents[2].id]

    @pytest.mark.parametrize(
        ("preset", "title", "available_roles", "expected_roles"),
        [
            ("code-delivery", "修复登录 Bug 并运行测试", ["planner", "coder", "reviewer"], ["coder", "reviewer"]),
            ("deep-research", "调研缓存方案并形成报告", ["planner", "research", "summarizer", "reviewer"], ["research", "summarizer"]),
            ("document-production", "根据现有材料编写正式文档", ["planner", "research", "summarizer", "reviewer"], ["research", "summarizer"]),
        ],
    )
    def test_team_preset_supplies_capabilities_without_forcing_a_role_sequence(self, client: TestClient, db_session, preset, title, available_roles, expected_roles):
        from src.models.agent import AgentStation
        from src.models.workspace import Task
        import uuid

        agents = [AgentStation(id=str(uuid.uuid4()), name=role.title(), role=role, default_model_id=f"{role}-model", is_enabled=True) for role in available_roles]
        db_session.add_all(agents)
        db_session.commit()

        goal_id = client.post("/api/v1/goals", json={"title": title, "team_preset": preset}).json()["data"]["goal_id"]
        response = client.post(f"/api/v1/goals/{goal_id}/start")
        assert response.status_code == 200, response.text
        tasks = db_session.query(Task).filter(Task.goal_id == goal_id).order_by(Task.priority.desc()).all()
        assigned_roles = [db_session.query(AgentStation).filter(AgentStation.id == task.assigned_agent_id).one().role for task in tasks]
        assert assigned_roles == expected_roles

    def test_simple_goal_does_not_activate_a_template_team(self, client: TestClient, db_session):
        from src.models.agent import AgentStation
        from src.models.workspace import ExecutionPlan, Task
        import uuid

        agents = [AgentStation(id=str(uuid.uuid4()), name=role.title(), role=role, default_model_id=f"{role}-model", is_enabled=True) for role in ["planner", "coder", "reviewer"]]
        db_session.add_all(agents); db_session.commit()
        goal_id = client.post("/api/v1/goals", json={"title": "解释什么是幂等性", "team_preset": "code-delivery"}).json()["data"]["goal_id"]
        assert client.post(f"/api/v1/goals/{goal_id}/start").status_code == 200
        assert db_session.query(Task).filter(Task.goal_id == goal_id).count() == 1
        plan = db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal_id).one()
        assert plan.task_mode == "direct"
        assert "did not force a role sequence" in plan.activation_reason

    def test_generated_serial_plan_executes_to_completion(self, client: TestClient, db_session):
        """The visible Workspace flow is backed by a runnable Runtime sequence."""
        from src.models.agent import AgentStation
        from src.models.model import Model
        import uuid

        agents = [
            AgentStation(id=str(uuid.uuid4()), name="Planner", role="planner", default_model_id="planner-model", is_enabled=True),
            AgentStation(id=str(uuid.uuid4()), name="Coder", role="coder", default_model_id="coder-model", is_enabled=True),
            AgentStation(id=str(uuid.uuid4()), name="Reviewer", role="reviewer", default_model_id="reviewer-model", is_enabled=True),
        ]
        models = [
            Model(id="planner-model", provider="mock", model_name="planner", display_name="Planner model", is_enabled=True),
            Model(id="coder-model", provider="mock", model_name="coder", display_name="Coder model", is_enabled=True),
            Model(id="reviewer-model", provider="mock", model_name="reviewer", display_name="Reviewer model", is_enabled=True),
        ]
        for model in models:
            model.set_capability_tags(["code", "reasoning", "planning", "review"])
        db_session.add_all([*agents, *models])
        db_session.commit()

        goal_id = client.post("/api/v1/goals", json={"title": "运行串行协作计划", "execution_mode": "mock"}).json()["data"]["goal_id"]
        assert client.post(f"/api/v1/goals/{goal_id}/start").status_code == 200
        planned_workspace = client.get(f"/api/v1/workspace/{goal_id}/state").json()["data"]
        assert planned_workspace["selection_decisions"]
        assert all(task["selection_decision"]["candidates"] for task in planned_workspace["tasks"])
        assert planned_workspace["multi_agent_metrics"]["why_multi_agent"] == planned_workspace["activation_reason"]

        unconfirmed = client.post(f"/api/v1/runtime/execute/{goal_id}")
        assert unconfirmed.status_code == 400
        assert "must be confirmed" in unconfirmed.json()["detail"]["error"]["message"]
        assert client.post(f"/api/v1/goals/{goal_id}/plans/1/confirm").status_code == 200

        execution = client.post(f"/api/v1/runtime/execute/{goal_id}")
        assert execution.status_code == 200, execution.text
        assert execution.json()["data"]["tasks_completed"] == 3, execution.json()
        # Mock output performed no file/test actions, so Runtime v2 creates a
        # real replan instead of declaring the code goal complete.
        assert execution.json()["data"]["status"] == "running"

        workspace = client.get(f"/api/v1/workspace/{goal_id}/state").json()["data"]
        # Mock-only execution has no file/tool evidence, so Runtime v2 must
        # never present it as verified completion.
        assert [task["status"] for task in workspace["tasks"][:3]] == ["completed_unverified", "completed_unverified", "completed_unverified"]
        assert all(task["title"].startswith("Revise:") for task in workspace["tasks"][3:]), [
            (task["title"], task["status"]) for task in workspace["tasks"]
        ]
        assert [task["flow_position"] for task in workspace["tasks"]] == list(range(1, len(workspace["tasks"]) + 1))

    def test_start_goal_not_found(self, client: TestClient):
        resp = client.post("/api/v1/goals/nonexistent/start")
        assert resp.status_code == 404

    def test_start_goal_requires_enabled_planner(self, client: TestClient):
        goal_id = client.post("/api/v1/goals", json={"title": "缺少 Planner 的 Goal"}).json()["data"]["goal_id"]
        response = client.post(f"/api/v1/goals/{goal_id}/start")
        assert response.status_code == 400
        assert "Planner" in response.json()["detail"]["error"]["message"]

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
        assert [task["flow_position"] for task in data["tasks"]] == [1, 2]
        assert len(data["agents"]) >= 1
        assert "workers" in data

    def test_workspace_state_not_found(self, client: TestClient):
        resp = client.get("/api/v1/workspace/nonexistent/state")
        assert resp.status_code == 404

    def test_workspace_task_handoff_is_available_in_workspace_state(self, client: TestClient, db_session):
        """A normal Workspace Task, not a legacy demo task, can be handed off end-to-end."""
        import uuid
        from src.models.agent import AgentStation
        from src.models.handoff import WorkerSession
        from src.models.workspace import Goal, Task

        from_agent = AgentStation(
            id=str(uuid.uuid4()), name="Coder", role="coder",
            default_model_id="model-gpt-4-turbo", status="running", is_enabled=True,
        )
        to_agent = AgentStation(
            id=str(uuid.uuid4()), name="Reviewer", role="reviewer",
            default_model_id="model-claude-3-5-sonnet", status="idle", is_enabled=True,
        )
        goal = Goal(id=str(uuid.uuid4()), title="Workspace handoff", status="running")
        worker = WorkerSession(
            id=str(uuid.uuid4()), agent_id=from_agent.id, model_id="model-gpt-4-turbo",
            goal_id=goal.id, task_id="pending-task-id", status="running",
        )
        task = Task(
            id=str(uuid.uuid4()), goal_id=goal.id, title="Implement auth", description="Add login flow",
            status="running", assigned_agent_id=from_agent.id, assigned_worker_id=worker.id,
            output="Login form is complete.",
        )
        worker.task_id = task.id
        db_session.add_all([from_agent, to_agent, goal, worker, task])
        db_session.commit()

        trigger = client.post(
            f"/api/v1/tasks/{task.id}/handoff",
            json={"to_agent_id": to_agent.id, "reason": "manual", "reason_description": "Please review the implementation."},
        )
        assert trigger.status_code == 201
        handoff_id = trigger.json()["data"]["handoff_id"]

        state = client.get(f"/api/v1/workspace/{goal.id}/state")
        assert state.status_code == 200
        task_data = state.json()["data"]["tasks"][0]
        assert task_data["status"] == "handoff"
        assert task_data["handoff"]["id"] == handoff_id
        assert task_data["handoff"]["from_agent_name"] == "Coder"
        assert task_data["handoff"]["to_agent_name"] == "Reviewer"

        accepted = client.post(f"/api/v1/handoffs/{handoff_id}/accept", json={})
        assert accepted.status_code == 200

        refreshed = client.get(f"/api/v1/workspace/{goal.id}/state").json()["data"]
        refreshed_task = refreshed["tasks"][0]
        assert refreshed_task["status"] == "running"
        assert refreshed_task["assigned_agent_id"] == to_agent.id
        assert refreshed_task["handoff"]["status"] == "accepted"

    def test_workspace_state_aggregates_router_quota_context_and_logs(self, client: TestClient, db_session):
        import uuid
        from src.models.agent import AgentStation
        from src.models.handoff import ExecutionLog, WorkerSession
        from src.models.quota import QuotaRecord
        from src.models.workspace import Goal, Task

        agent = AgentStation(
            id=str(uuid.uuid4()), name="Coder", role="coder",
            default_model_id="model-gpt-4-turbo", status="running", is_enabled=True,
        )
        goal = Goal(id=str(uuid.uuid4()), title="Workspace details", status="running")
        task = Task(
            id=str(uuid.uuid4()), goal_id=goal.id, title="Build dashboard", status="running",
            assigned_agent_id=agent.id,
        )
        worker = WorkerSession(
            id=str(uuid.uuid4()), agent_id=agent.id, model_id="model-gpt-4-turbo",
            goal_id=goal.id, task_id=task.id, status="running", current_context='{"project":"ModelGate"}',
        )
        task.assigned_worker_id = worker.id
        quota = QuotaRecord(
            id=str(uuid.uuid4()), provider="openai", model_id="model-gpt-4-turbo", model_name="GPT-4 Turbo",
            quota_status="warning", usage_percent=0.8, total_tokens=800, token_limit=1000,
        )
        log = ExecutionLog(
            id=str(uuid.uuid4()), goal_id=goal.id, task_id=task.id, agent_id=agent.id,
            model_id="model-gpt-4-turbo", event_type="model_call", event_status="completed",
            output_summary="Generated dashboard plan.",
        )
        log.set_routing_info({
            "selected_model_id": "model-gpt-4-turbo",
            "confidence": 0.91,
            "routing_reason": {"summary": "Strong coding match", "primary_factors": ["code"]},
            "backup_model_ids": ["model-deepseek-coder"],
        })
        db_session.add_all([agent, goal, task, worker, quota, log])
        db_session.commit()

        response = client.get(f"/api/v1/workspace/{goal.id}/state")
        assert response.status_code == 200
        data = response.json()["data"]["tasks"][0]
        assert data["context"] == '{"project":"ModelGate"}'
        assert data["quota"]["quota_status"] == "warning"
        assert data["routing_decision"]["confidence"] == 0.91
        assert data["routing_decision"]["routing_reason"]["summary"] == "Strong coding match"
        assert data["recent_logs"][0]["output_summary"] == "Generated dashboard plan."
