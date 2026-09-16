"""V1.4 T3: incremental resume.

A task re-entering execution with checkpoints continues from its last
stable state (checkpoint restore fires) instead of replaying from
scratch; worktree tasks are excluded because their checkpoints reference
primary-workspace paths.
"""
import uuid

import pytest

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.workspace import Goal, Task, WorkspaceCheckpoint
from src.services import runtime_service
from src.services.providers.base import ModelResponse
from src.services.providers.provider_factory import create_provider, set_provider


class OneResponseProvider:
    async def generate(self, _request):
        return ModelResponse(
            content="resumed work completed", input_tokens=2, output_tokens=2,
            total_tokens=4, latency_ms=1, finish_reason="stop",
        )


@pytest.fixture
def _pending_task_with_checkpoint(db_session, tmp_path, monkeypatch):
    agent = AgentStation(
        id=str(uuid.uuid4()), name="Resume Coder", role="coder",
        default_model_id="model-claude-opus", is_enabled=True,
        system_prompt="work",
    )
    goal = Goal(
        id=str(uuid.uuid4()), title="Resume goal", status="running",
        execution_mode="mock", workspace_root=str(tmp_path),
    )
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Resume task",
        description="incremental resume", status="pending",
        assigned_agent_id=agent.id,
    )
    db_session.add_all([agent, goal, task])
    db_session.commit()

    checkpoint_file = tmp_path / "resumable.py"
    checkpoint_file.write_text("stable = True\n")
    checkpoint = WorkspaceCheckpoint(
        goal_id=goal.id, task_id=task.id,
        path=str(checkpoint_file), content="stable = True\n", existed=True,
    )
    db_session.add(checkpoint)
    db_session.commit()

    calls = []
    original = runtime_service._restore_task_checkpoints

    def spy(db, task_arg):
        calls.append(task_arg.id)
        return original(db, task_arg)

    monkeypatch.setattr(runtime_service, "_restore_task_checkpoints", spy)
    return goal, task, calls


def _mock_provider():
    set_provider(OneResponseProvider())


def test_pending_reentry_restores_checkpoints(db_session, _pending_task_with_checkpoint):
    goal, task, calls = _pending_task_with_checkpoint
    _mock_provider()
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
        assert result["status"] in {"completed", "completed_verified", "completed_unverified"}
        assert calls == [task.id], "checkpoint restore must fire on pending re-entry"
        resumed_log = db_session.query(ExecutionLog).filter(
            ExecutionLog.task_id == task.id,
            ExecutionLog.event_type == "task.checkpoint_resumed",
        ).one()
        assert len(resumed_log.get_metadata()["paths"]) == 1
    finally:
        set_provider(create_provider("mock"))


def test_worktree_tasks_skip_checkpoint_restore(db_session, _pending_task_with_checkpoint, tmp_path):
    goal, task, calls = _pending_task_with_checkpoint
    task.set_json("required_capabilities", ["parallel_safe"])
    db_session.commit()
    _mock_provider()
    try:
        runtime_service.execute_task_step(db_session, task.id)
        assert calls == [], "worktree tasks must not restore primary-workspace checkpoints"
    finally:
        set_provider(create_provider("mock"))
