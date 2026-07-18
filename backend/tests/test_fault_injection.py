import asyncio
import hashlib
import json
import subprocess
import uuid

import pytest
from sqlalchemy.exc import OperationalError

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.model import Model
from src.models.workspace import Goal, Task
from src.services import runtime_service, tool_service, verifier_service
from src.services.providers.base import ModelResponse
from src.services.providers.provider_factory import create_provider, set_provider
from src.services.state_machine_service import transition_goal
from src.services.tool_service import ToolExecutor, seed_builtin_tools


class OneResponseProvider:
    async def generate(self, _request):
        return ModelResponse(
            content="work attempted", input_tokens=2, output_tokens=2,
            total_tokens=4, latency_ms=1, finish_reason="stop",
        )


def _tool_scope(db_session, root, tool_name):
    agent = AgentStation(
        id=str(uuid.uuid4()), name="Fault Agent", role="coder",
        default_model_id="fault-model", is_enabled=True,
    )
    agent.set_allowed_tools([tool_name])
    goal = Goal(
        id=str(uuid.uuid4()), title="Fault injection", status="running",
        execution_mode="mock", workspace_root=str(root),
    )
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Faulty tool",
        status="pending", assigned_agent_id=agent.id,
    )
    db_session.add_all([agent, goal, task])
    seed_builtin_tools(db_session)
    db_session.commit()
    return agent, goal, task


def test_tool_timeout_is_failed_and_audited(db_session, tmp_path, monkeypatch):
    agent, goal, task = _tool_scope(db_session, tmp_path, "test_runner")

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("pytest", 1)

    monkeypatch.setattr(tool_service.subprocess, "run", timeout)
    record = asyncio.run(ToolExecutor().execute(
        db_session, "test_runner", {"command": "pytest -q"},
        goal.id, task.id, agent.id, "worker",
    ))
    assert record.status == "failed"
    assert "timed out" in record.error_message
    assert record.get_result()["exit_code"] is None
    assert db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_status == "failed",
    ).count() == 1


def test_tool_nonzero_build_exit_is_not_completed(db_session, tmp_path, monkeypatch):
    agent, goal, task = _tool_scope(db_session, tmp_path, "build_run")
    monkeypatch.setattr(
        tool_service.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 2, "", "build failed"),
    )
    record = asyncio.run(ToolExecutor().execute(
        db_session, "build_run", {"command": "npm run build"},
        goal.id, task.id, agent.id, "worker",
    ))
    assert record.status == "failed"
    assert record.get_result()["exit_code"] == 2
    assert "build failed" in record.get_result()["stderr"]


@pytest.mark.parametrize("failure", [PermissionError("permission denied"), OSError(28, "disk full")])
def test_file_write_os_failures_are_visible_and_leave_no_artifact(
    db_session, tmp_path, monkeypatch, failure,
):
    agent, goal, task = _tool_scope(db_session, tmp_path, "file_write")

    def fail_write(**_kwargs):
        raise failure

    monkeypatch.setitem(tool_service.TOOL_EXECUTORS, "file_write", fail_write)
    record = asyncio.run(ToolExecutor().execute(
        db_session, "file_write", {"path": "result.txt", "content": "data"},
        goal.id, task.id, agent.id, "worker",
    ))
    assert record.status == "failed"
    assert str(failure) in record.error_message
    assert not (tmp_path / "result.txt").exists()


def test_file_patch_detects_concurrent_modification(tmp_path):
    target = tmp_path / "module.py"
    original = "value = 1\n"
    target.write_text(original, encoding="utf-8")
    stale_checksum = hashlib.sha256(original.encode()).hexdigest()
    target.write_text("value = 2\n", encoding="utf-8")

    result = tool_service._file_patch(
        "module.py", "value = 1", "value = 3",
        expected_checksum=stale_checksum, cwd=str(tmp_path),
    )
    assert result["success"] is False
    assert result["conflict"] == "concurrent_modification"
    assert target.read_text(encoding="utf-8") == "value = 2\n"


def test_worktree_creation_failure_blocks_parallel_task_with_visible_reason(db_session, tmp_path):
    agent = AgentStation(
        id=str(uuid.uuid4()), name="Parallel", role="coder",
        default_model_id="parallel-model", is_enabled=True,
    )
    model = Model(
        id="parallel-model", provider="mock", model_name="parallel-model",
        display_name="Parallel", is_enabled=True,
    )
    goal = Goal(
        id=str(uuid.uuid4()), title="Parallel fault", status="running",
        execution_mode="mock", workspace_root=str(tmp_path),
    )
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Parallel edit",
        task_type="coding", status="pending", assigned_agent_id=agent.id,
    )
    task.set_json("required_capabilities", ["parallel_safe", "code_edit"])
    db_session.add_all([agent, model, goal, task])
    db_session.commit()

    result = runtime_service.execute_task_step(db_session, task.id)

    db_session.refresh(task)
    assert result["status"] == "blocked"
    assert task.status == "blocked"
    assert "Git workspace root" in task.blocked_reason
    error = db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "worktree_created",
    ).one()
    assert error.event_status == "failed"


def test_database_disconnect_rolls_back_state_and_event(db_session, monkeypatch):
    goal = Goal(id=str(uuid.uuid4()), title="Disconnect", status="idle")
    db_session.add(goal)
    db_session.commit()
    original_commit = db_session.commit
    calls = 0

    def disconnect_once():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OperationalError("COMMIT", {}, RuntimeError("connection lost"))
        return original_commit()

    monkeypatch.setattr(db_session, "commit", disconnect_once)
    with pytest.raises(OperationalError):
        transition_goal(db_session, goal, "planning", summary="start")
    db_session.refresh(goal)
    assert goal.status == "idle"
    assert db_session.query(ExecutionLog).filter(ExecutionLog.goal_id == goal.id).count() == 0


def test_verification_write_failure_marks_task_failed_and_never_completed(
    db_session, tmp_path, monkeypatch,
):
    agent = AgentStation(
        id=str(uuid.uuid4()), name="Verifier fault", role="summarizer",
        default_model_id="verify-model", is_enabled=True,
    )
    model = Model(
        id="verify-model", provider="mock", model_name="verify-model",
        display_name="Verify", is_enabled=True,
    )
    goal = Goal(
        id=str(uuid.uuid4()), title="Verification fault", status="running",
        execution_mode="mock", workspace_root=str(tmp_path),
    )
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Answer",
        task_type="direct", status="pending", assigned_agent_id=agent.id,
    )
    db_session.add_all([agent, model, goal, task])
    db_session.commit()

    def fail_verification(_db, _task):
        raise OperationalError("INSERT verification", {}, RuntimeError("deadlock detected"))

    monkeypatch.setattr(verifier_service, "verify_task_contract", fail_verification)
    set_provider(OneResponseProvider())
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))

    db_session.refresh(task)
    assert result["status"] == "failed"
    assert task.status == "failed"
    assert "Verification persistence failed" in db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "error",
    ).one().error_message


def test_tool_input_secret_is_redacted_but_execution_uses_original_value(db_session, tmp_path):
    agent, goal, task = _tool_scope(db_session, tmp_path, "file_write")
    secret = "api_key=sk_live_1234567890abcdefghijkl"
    record = asyncio.run(ToolExecutor().execute(
        db_session, "file_write", {"path": "output.txt", "content": secret},
        goal.id, task.id, agent.id, "worker",
    ))
    assert record.status == "completed"
    assert "[REDACTED]" in json.dumps(record.get_tool_input())
    assert (tmp_path / "output.txt").read_text(encoding="utf-8") == secret
