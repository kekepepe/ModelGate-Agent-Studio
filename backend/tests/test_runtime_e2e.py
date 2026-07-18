"""Runtime E2E integration tests.

Three core E2E tests as specified by the roadmap:
  1. Normal Goal execution completes
  2. Quota risk triggers Handoff
  3. execute-step only affects single task
"""

import uuid
from fastapi.testclient import TestClient


def _seed_e2e_data(db_session):
    """Create full E2E test data: agents, models, goal, tasks."""
    from src.models.agent import AgentStation
    from src.models.model import Model
    from src.models.workspace import Goal, Task

    planner = AgentStation(
        id=str(uuid.uuid4()), name="Planner", role="planner",
        default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True,
        system_prompt="Plan tasks carefully.",
    )
    coder = AgentStation(
        id=str(uuid.uuid4()), name="Coder", role="coder",
        default_model_id="model-claude-opus", status="idle", is_enabled=True,
        system_prompt="Write clean code.",
    )
    reviewer = AgentStation(
        id=str(uuid.uuid4()), name="Reviewer", role="reviewer",
        default_model_id="model-claude-3-haiku", status="idle", is_enabled=True,
    )
    db_session.add_all([planner, coder, reviewer])

    models = [
        Model(id="model-gpt-4-turbo", provider="openai", model_name="gpt-4-turbo",
              display_name="GPT-4 Turbo", is_enabled=True, max_context_tokens=128000,
              cost_level=4, speed_level=3),
        Model(id="model-claude-opus", provider="anthropic", model_name="claude-3-opus",
              display_name="Claude 3 Opus", is_enabled=True, max_context_tokens=200000,
              cost_level=5, speed_level=3),
        Model(id="model-claude-3-haiku", provider="anthropic", model_name="claude-3-haiku",
              display_name="Claude 3 Haiku", is_enabled=True, max_context_tokens=200000,
              cost_level=1, speed_level=1),
    ]
    for m in models:
        m.set_capability_tags(["code", "reasoning"])
        db_session.add(m)
    db_session.commit()

    goal = Goal(id=str(uuid.uuid4()), title="E2E Build Auth System", status="planning")
    db_session.add(goal)
    db_session.commit()

    planner_task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Plan architecture",
        description="Plan the auth system architecture", status="pending",
        assigned_agent_id=planner.id,
    )
    code_task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Build login page",
        description="Implement the login form with validation", status="pending",
        assigned_agent_id=coder.id,
    )
    review_task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Review implementation",
        description="Review code quality and security", status="pending",
        assigned_agent_id=reviewer.id,
    )
    db_session.add_all([planner_task, code_task, review_task])
    db_session.commit()
    return goal, [planner_task, code_task, review_task], [planner, coder, reviewer]


class TestE2ENormalExecution:
    """E2E 1: Normal Goal execution completes."""

    def test_full_execution_all_tasks_completed(self, client: TestClient, db_session):
        goal, tasks, _ = _seed_e2e_data(db_session)

        resp = client.post(f"/api/v1/runtime/execute/{goal.id}")
        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["status"] == "completed"
        assert result["tasks_completed"] == 3
        assert result["tasks_failed"] == 0
        assert result["total_tokens_used"] > 0

        # Verify goal status
        status_resp = client.get(f"/api/v1/runtime/status/{goal.id}")
        assert status_resp.status_code == 200
        status = status_resp.json()["data"]
        assert status["goal_status"] == "completed"
        assert status["completed_tasks"] == 3
        assert status["log_count"] > 0
        assert status["model_call_count"] > 0

        # Verify WorkerSessions created
        from src.models.handoff import WorkerSession
        workers = db_session.query(WorkerSession).filter(
            WorkerSession.goal_id == goal.id
        ).all()
        assert len(workers) >= 3

        # Verify execution logs created
        from src.models.handoff import ExecutionLog
        logs = db_session.query(ExecutionLog).filter(
            ExecutionLog.goal_id == goal.id
        ).all()
        assert len(logs) > 0
        assert "goal.completed" in {item.event_type for item in logs}

        # Verify quota records
        from src.models.quota import QuotaRecord
        quotas = db_session.query(QuotaRecord).all()
        assert len(quotas) >= 1


class TestE2EQuotaHandoff:
    """E2E 2: Quota risk triggers Handoff."""

    def test_quota_intercept_triggers_handoff(self, client: TestClient, db_session):
        from src.models.quota import QuotaRecord
        from src.models.model import Model

        # Disable other coding models so router MUST pick opus (which is quota-limited)
        for mid in ["model-claude-3-haiku", "model-deepseek-coder", "model-gpt-4-turbo"]:
            m = db_session.query(Model).filter(Model.id == mid).first()
            if m:
                m.is_enabled = False
        db_session.commit()

        # Set up quota record with LIMITED status for claude-3-opus
        quota = QuotaRecord(
            id=str(uuid.uuid4()),
            provider="anthropic",
            model_id="model-claude-opus",
            model_name="Claude 3 Opus",
            quota_mode="known",
            quota_status="limited",
            usage_percent=1.0,
            token_limit=1000,
            total_tokens=1000,
            estimated_remaining=0,
        )
        db_session.add(quota)
        db_session.commit()

        goal, tasks, agents = _seed_e2e_data(db_session)
        # Find the coder task (assigned to coder agent with default model claude-3-opus)
        coder_task = [t for t in tasks if t.assigned_agent_id == agents[1].id][0]

        resp = client.post(f"/api/v1/runtime/execute-step/{coder_task.id}")
        assert resp.status_code == 200
        result = resp.json()["data"]
        # Task should be handed off because model is limited
        assert result["is_handoff"] is True
        assert result["status"] == "handoff"

        # Verify HandoffRecord created
        from src.models.handoff import HandoffRecord
        handoffs = db_session.query(HandoffRecord).filter(
            HandoffRecord.goal_id == goal.id
        ).all()
        assert len(handoffs) >= 1

        # Verify task status
        db_session.refresh(coder_task)
        assert coder_task.status == "handoff"

        # Verify handoff reason logged
        from src.models.handoff import ExecutionLog
        handoff_logs = db_session.query(ExecutionLog).filter(
            ExecutionLog.goal_id == goal.id,
            ExecutionLog.event_type.in_(["handoff_created", "handoff_completed"]),
        ).all()
        assert len(handoff_logs) >= 1


class TestE2EProviderFailureHandoff:
    """E2E 3: provider errors produce a resumable Handoff rather than a dead task."""

    def test_provider_error_handoff_can_be_accepted_and_resumed(self, client: TestClient, db_session):
        from src.models.handoff import HandoffRecord
        from src.models.model import Model
        from src.services import router_service
        from src.services.providers.mock_provider import MockModelProvider
        from src.services.providers.provider_factory import create_provider, set_provider

        goal, tasks, agents = _seed_e2e_data(db_session)
        task = [item for item in tasks if item.assigned_agent_id == agents[1].id][0]
        routing = router_service.select_model(
            db=db_session, task_id=task.id, task_type="coding", preferred_agent_id=agents[1].id,
        )
        assert routing["backup_model_ids"]

        failing_provider = MockModelProvider(default_latency_ms=0)
        selected_model = db_session.query(Model).filter(Model.id == routing["selected_model_id"]).one()
        failing_provider.configure_model(selected_model.model_name, raise_error="Provider timeout")
        set_provider(failing_provider)
        try:
            failed_run = client.post(f"/api/v1/runtime/execute-step/{task.id}")
            assert failed_run.status_code == 200
            assert failed_run.json()["data"]["status"] == "handoff"
            assert failed_run.json()["data"]["is_handoff"] is True

            goal.status = "handoff"
            db_session.commit()
            handoff = db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).one()
            assert handoff.reason == "error"
            accepted = client.post(f"/api/v1/handoffs/{handoff.id}/accept", json={})
            assert accepted.status_code == 200
            db_session.refresh(goal)
            assert goal.status == "running"

            resumed_run = client.post(f"/api/v1/runtime/execute-step/{task.id}")
            assert resumed_run.status_code == 200, resumed_run.text
            assert resumed_run.json()["data"]["status"] == "completed"
            assert resumed_run.json()["data"]["is_handoff"] is False
        finally:
            set_provider(create_provider("mock"))


class TestE2ESingleStep:
    """E2E 3: execute-step only affects single task."""

    def test_single_step_only_affects_target_task(self, client: TestClient, db_session):
        goal, tasks, _ = _seed_e2e_data(db_session)

        target = tasks[1]  # code task
        other = tasks[2]   # review task

        resp = client.post(f"/api/v1/runtime/execute-step/{target.id}")
        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["status"] == "completed"
        assert result["task_id"] == target.id

        # Verify target task completed
        from src.models.workspace import Task
        db_session.refresh(db_session.query(Task).filter(Task.id == target.id).first())
        target_refreshed = db_session.query(Task).filter(Task.id == target.id).first()
        assert target_refreshed.status == "completed"

        # Verify other task still pending
        other_refreshed = db_session.query(Task).filter(Task.id == other.id).first()
        assert other_refreshed.status == "pending"

        # Verify execution logs only for target task
        from src.models.handoff import ExecutionLog
        target_logs = db_session.query(ExecutionLog).filter(
            ExecutionLog.task_id == target.id
        ).count()
        other_logs = db_session.query(ExecutionLog).filter(
            ExecutionLog.task_id == other.id
        ).count()
        assert target_logs > 0
        assert other_logs == 0

        # Verify RuntimeStatus reflects partial progress
        status_resp = client.get(f"/api/v1/runtime/status/{goal.id}")
        assert status_resp.status_code == 200
        status = status_resp.json()["data"]
        assert status["completed_tasks"] == 1
        assert status["total_tasks"] == 3

    def test_single_step_no_side_effects(self, client: TestClient, db_session):
        """Frontend should have no errors when calling execute-step (API test)."""
        _, tasks, _ = _seed_e2e_data(db_session)
        resp = client.post(f"/api/v1/runtime/execute-step/{tasks[0].id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "error" not in data
