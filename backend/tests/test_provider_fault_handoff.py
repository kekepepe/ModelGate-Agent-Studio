"""V1.3 P2 T6: provider faults drive the backup/handoff mechanism.

Real provider failures (429 / 5xx / 529 overload / timeout — exactly the
AnthropicProviderError and OpenAICompatibleError classifications) must
flow through runtime_service._handle_task_failure: with backup routing +
a second enabled station they become a handoff (reason=error); without
backup they become a plain failed task. These tests pin the decision
mechanism that e2e-live-provider.sh later exercises with real keys.
"""
import uuid

import pytest

from src.models.agent import AgentStation
from src.models.handoff import HandoffRecord, WorkerSession
from src.models.workspace import Goal, Task
from src.services.providers.base import ProviderError
from src.services.runtime_service import _handle_task_failure


def _seed(db_session, *, with_backup=True):
    first = AgentStation(
        id=str(uuid.uuid4()), name="Coder A", role="coder",
        default_model_id="model-a", is_enabled=True,
    )
    second = AgentStation(
        id=str(uuid.uuid4()), name="Coder B", role="coder",
        default_model_id="model-b", is_enabled=True,
    ) if with_backup else None
    goal = Goal(id=str(uuid.uuid4()), title="Fault goal", status="running")
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Break something",
        description="provokes a provider fault", status="running",
        assigned_agent_id=first.id,
    )
    worker = WorkerSession(
        agent_id=first.id, model_id=first.default_model_id,
        goal_id=goal.id, task_id=task.id, status="running",
    )
    rows = [first, goal, task, worker] + ([second] if second else [])
    db_session.add_all(rows)
    db_session.commit()
    routing = {"backup_model_ids": ["model-b"]} if with_backup else {"backup_model_ids": []}
    return goal, task, first, second, worker, routing


def _provider_error(code: str, retryable: bool) -> ProviderError:
    return ProviderError(code, f"provider fault: {code}", retryable=retryable)


@pytest.mark.parametrize(
    "code, retryable",
    [
        ("provider_rate_limited", True),   # 429
        ("provider_unavailable", True),    # 5xx / 529 overloaded
        ("provider_timeout", True),        # 408/504
        ("provider_auth_error", False),    # 401/403 — backup may have valid creds
    ],
)
def test_provider_faults_become_handoff_with_backup(db_session, code, retryable):
    goal, task, agent, second, worker, routing = _seed(db_session, with_backup=True)

    result = _handle_task_failure(
        db_session, task, agent, worker,
        str(_provider_error(code, retryable)), routing,
    )

    assert result["status"] == "handoff"
    assert result["is_handoff"] is True
    handoff = db_session.query(HandoffRecord).filter(HandoffRecord.task_id == task.id).one()
    assert handoff.reason == "error"
    assert handoff.status == "ready"


def test_provider_fault_without_backup_fails_the_task(db_session):
    goal, task, agent, second, worker, routing = _seed(db_session, with_backup=False)

    result = _handle_task_failure(
        db_session, task, agent, worker,
        str(_provider_error("provider_rate_limited", True)), routing,
    )

    assert result["status"] == "failed"
    assert db_session.query(HandoffRecord).count() == 0
    db_session.refresh(task)
    assert task.status == "failed"


def test_worker_failure_metadata_recorded_on_handoff(db_session):
    goal, task, agent, second, worker, routing = _seed(db_session, with_backup=True)
    error = _provider_error("provider_timeout", True)

    _handle_task_failure(db_session, task, agent, worker, str(error), routing)

    db_session.refresh(worker)
    assert worker.status == "failed"
    assert "provider fault" in (worker.error_message or "")
