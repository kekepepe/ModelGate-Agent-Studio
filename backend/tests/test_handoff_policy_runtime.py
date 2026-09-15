"""V1.1: station handoff_policy gates the runtime auto-triggers.

No explicit policy JSON keeps the pre-V1.1 behavior (auto-handoff on
provider error with backup routing, auto-handoff on quota intercept,
blocked+replan on quality failure). An explicit ``handoff_policy`` JSON on
the station is authoritative: can_initiate=false disables auto handoff,
on_provider_error supports retry_once/fail/handoff, on_quota_exhausted
supports handoff/fail/fallback_backup, and on_quality_issue=handoff
transfers the task after the verification retry budget is exhausted.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from src.models.handoff import HandoffRecord
from src.models.model import Model
from src.models.quota import QuotaRecord
from src.services.providers.mock_provider import MockModelProvider
from src.services.providers.provider_factory import set_provider


@pytest.fixture
def _seed(db_session):
    """Planner/coder/reviewer stations + models + a planning goal, e2e style."""
    from src.models.agent import AgentStation
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
    db_session.add_all(models)

    goal = Goal(id=str(uuid.uuid4()), title="Policy Goal", status="planning")
    db_session.add(goal)
    db_session.commit()

    code_task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Build login page",
        description="Implement the login form with validation", status="pending",
        assigned_agent_id=coder.id,
    )
    db_session.add(code_task)
    db_session.commit()
    return goal, code_task, coder, reviewer


def _force_router_to_opus(db_session):
    for mid in ["model-claude-3-haiku", "model-deepseek-coder", "model-gpt-4-turbo"]:
        m = db_session.query(Model).filter(Model.id == mid).first()
        if m:
            m.is_enabled = False
    db_session.commit()


def _failing_provider(db_session):
    provider = MockModelProvider(default_latency_ms=0)
    selected = db_session.query(Model).filter(Model.id == "model-claude-opus").one()
    provider.configure_model(selected.model_name, raise_error="Provider timeout")
    set_provider(provider)


class TestProviderErrorPolicy:
    def test_no_policy_keeps_legacy_error_handoff(self, client: TestClient, db_session, _seed):
        goal, task, coder, _ = _seed
        _failing_provider(db_session)
        resp = client.post(f"/api/v1/runtime/execute-step/{task.id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["is_handoff"] is True
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).one().reason == "error"

    def test_can_initiate_false_blocks_error_handoff(self, client: TestClient, db_session, _seed):
        goal, task, coder, _ = _seed
        coder.set_handoff_policy({"can_initiate": False})
        db_session.commit()
        _failing_provider(db_session)

        resp = client.post(f"/api/v1/runtime/execute-step/{task.id}")

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "failed"
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).count() == 0
        db_session.refresh(task)
        assert task.status == "failed"

    def test_on_provider_error_fail_skips_handoff(self, client: TestClient, db_session, _seed):
        goal, task, coder, _ = _seed
        coder.set_handoff_policy({"on_provider_error": "fail"})
        db_session.commit()
        _failing_provider(db_session)

        resp = client.post(f"/api/v1/runtime/execute-step/{task.id}")

        assert resp.json()["data"]["status"] == "failed"
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).count() == 0

    def test_retry_once_requeues_then_fails(self, client: TestClient, db_session, _seed):
        goal, task, coder, _ = _seed
        coder.set_handoff_policy({"on_provider_error": "retry_once"})
        db_session.commit()
        _failing_provider(db_session)

        first = client.post(f"/api/v1/runtime/execute-step/{task.id}")
        assert first.status_code == 200
        assert first.json()["data"]["status"] == "pending"
        db_session.refresh(task)
        assert task.status == "pending"
        from src.models.handoff import ExecutionLog
        assert db_session.query(ExecutionLog).filter(
            ExecutionLog.task_id == task.id,
            ExecutionLog.event_type == "error",
            ExecutionLog.event_status == "retry_scheduled",
        ).count() == 1
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).count() == 0

        second = client.post(f"/api/v1/runtime/execute-step/{task.id}")
        assert second.status_code == 200
        assert second.json()["data"]["status"] == "failed"
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).count() == 0


class TestQuotaPolicy:
    def _limit_opus(self, db_session):
        _force_router_to_opus(db_session)
        db_session.add(QuotaRecord(
            id=str(uuid.uuid4()), provider="anthropic", model_id="model-claude-opus",
            model_name="Claude 3 Opus", quota_mode="known", quota_status="limited",
            usage_percent=1.0, token_limit=1000, total_tokens=1000, estimated_remaining=0,
        ))
        db_session.commit()

    def test_fallback_backup_requeues_once_then_fails(self, client: TestClient, db_session, _seed):
        goal, task, coder, _ = _seed
        coder.set_handoff_policy({"on_quota_exhausted": "fallback_backup"})
        db_session.commit()
        self._limit_opus(db_session)

        first = client.post(f"/api/v1/runtime/execute-step/{task.id}")
        assert first.status_code == 200
        assert first.json()["data"]["status"] == "pending"
        db_session.refresh(task)
        from src.models.handoff import ExecutionLog
        assert db_session.query(ExecutionLog).filter(
            ExecutionLog.task_id == task.id,
            ExecutionLog.event_type == "task.blocked",
            ExecutionLog.event_status == "requeued",
        ).count() == 1
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).count() == 0

        second = client.post(f"/api/v1/runtime/execute-step/{task.id}")
        assert second.status_code == 200
        assert second.json()["data"]["status"] == "failed"
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).count() == 0

    def test_on_quota_exhausted_fail_skips_handoff(self, client: TestClient, db_session, _seed):
        goal, task, coder, _ = _seed
        coder.set_handoff_policy({"on_quota_exhausted": "fail"})
        db_session.commit()
        self._limit_opus(db_session)

        resp = client.post(f"/api/v1/runtime/execute-step/{task.id}")

        assert resp.json()["data"]["status"] == "failed"
        assert resp.json()["data"]["quota_status"] == "limited"
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).count() == 0

    def test_can_initiate_false_blocks_quota_handoff(self, client: TestClient, db_session, _seed):
        goal, task, coder, _ = _seed
        coder.set_handoff_policy({"can_initiate": False})
        db_session.commit()
        self._limit_opus(db_session)

        resp = client.post(f"/api/v1/runtime/execute-step/{task.id}")

        assert resp.json()["data"]["status"] == "failed"
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).count() == 0

    def test_quota_handoff_increments_handoff_triggered_count(self, client: TestClient, db_session, _seed):
        from src.models.quota import QuotaRecord as QuotaRecordModel

        goal, task, coder, _ = _seed
        self._limit_opus(db_session)

        resp = client.post(f"/api/v1/runtime/execute-step/{task.id}")

        assert resp.json()["data"]["is_handoff"] is True
        record = db_session.query(QuotaRecordModel).filter(QuotaRecordModel.model_id == "model-claude-opus").one()
        assert record.handoff_triggered_count == 1


class TestQualityIssuePolicy:
    def test_on_quality_issue_handoff_transfers_task(self, db_session, _seed):
        from src.models.handoff import WorkerSession

        goal, task, coder, reviewer = _seed
        coder.set_handoff_policy({"on_quality_issue": "handoff"})
        task.status = "running"
        worker = WorkerSession(
            agent_id=coder.id, model_id=coder.default_model_id, goal_id=goal.id,
            task_id=task.id, status="running",
        )
        db_session.add(worker)
        db_session.commit()

        from src.services.runtime_service import _maybe_handoff_on_quality
        outcome = _maybe_handoff_on_quality(
            db_session, task, coder, routing=None,
            verification={"status": "failed", "results": [{"criterion": "diff_exists", "status": "failed"}]},
        )

        assert outcome is not None
        handoff = db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).one()
        assert handoff.reason == "quality_issue"
        assert handoff.status == "ready"
        db_session.refresh(task)
        assert task.status == "handoff"

    def test_default_policy_keeps_replan_behavior(self, db_session, _seed):
        goal, task, coder, reviewer = _seed
        task.status = "running"
        db_session.commit()

        from src.services.runtime_service import _maybe_handoff_on_quality
        outcome = _maybe_handoff_on_quality(
            db_session, task, coder, routing=None,
            verification={"status": "failed", "results": []},
        )

        assert outcome is None
        assert db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).count() == 0
