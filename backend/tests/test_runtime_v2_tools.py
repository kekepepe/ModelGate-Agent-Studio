import asyncio
import os
import tempfile
import uuid

import pytest

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.workspace import Goal, Task, WorkspaceCheckpoint
from src.services.tool_service import ToolExecutor, ToolPolicyError, seed_builtin_tools
from src.services.workspace_service import get_workspace_state


def _scope(db_session, root):
    agent = AgentStation(id=str(uuid.uuid4()), name="Coder", role="coder", default_model_id="test-model", is_enabled=True)
    agent.set_allowed_tools(["file_write", "file_patch", "checkpoint_restore", "checkpoint_create"])
    goal = Goal(id=str(uuid.uuid4()), title="Tool test", status="running", execution_mode="sandbox", workspace_root=root)
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Edit", assigned_agent_id=agent.id)
    db_session.add_all([agent, goal, task])
    seed_builtin_tools(db_session)
    db_session.commit()
    return agent, goal, task


def test_file_write_creates_checkpoint_and_restore_reverts(db_session):
    with tempfile.TemporaryDirectory() as root:
        path = os.path.join(root, "sample.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("value = 1\n")
        agent, goal, task = _scope(db_session, root)
        executor = ToolExecutor()
        write = asyncio.run(executor.execute(db_session, "file_write", {"path": "sample.py", "content": "value = 2\n"}, goal.id, task.id, agent.id, "worker"))
        assert write.status == "completed"
        event = db_session.query(ExecutionLog).filter(ExecutionLog.task_id == task.id, ExecutionLog.tool_name == "file_write").one()
        assert event.event_status == "completed"
        checkpoint = db_session.query(WorkspaceCheckpoint).filter(WorkspaceCheckpoint.task_id == task.id).one()
        assert checkpoint.content == "value = 1\n"
        restored = asyncio.run(executor.execute(db_session, "checkpoint_restore", {"path": "sample.py"}, goal.id, task.id, agent.id, "worker"))
        assert restored.status == "completed"
        assert open(path, encoding="utf-8").read() == "value = 1\n"


def test_workspace_tool_rejects_path_escape(db_session):
    with tempfile.TemporaryDirectory() as root:
        agent, goal, task = _scope(db_session, root)
        denied = asyncio.run(ToolExecutor().execute(db_session, "file_write", {"path": "../outside.txt", "content": "no"}, goal.id, task.id, agent.id, "worker"))
        assert denied.status == "denied"
        assert "escapes" in (denied.error_message or "")
        event = db_session.query(ExecutionLog).filter(ExecutionLog.task_id == task.id, ExecutionLog.tool_name == "file_write").one()
        assert event.event_status == "denied"


def test_workspace_search_rejects_parent_glob_escape(db_session):
    with tempfile.TemporaryDirectory() as root:
        agent, goal, task = _scope(db_session, root)
        agent.set_allowed_tools(["file_search"])
        db_session.commit()
        denied = asyncio.run(ToolExecutor().execute(db_session, "file_search", {"pattern": "../*"}, goal.id, task.id, agent.id, "worker"))
        assert denied.status == "denied"
        assert "escapes" in (denied.error_message or "")


def test_agent_tool_permission_denial_is_auditable(db_session):
    with tempfile.TemporaryDirectory() as root:
        agent, goal, task = _scope(db_session, root)
        agent.set_allowed_tools(["file_read"])
        db_session.commit()
        denied = asyncio.run(ToolExecutor().execute(db_session, "file_write", {"path": "blocked.py", "content": "x = 1\n"}, goal.id, task.id, agent.id, "worker"))
        assert denied.status == "denied"
        assert "not allowed" in (denied.error_message or "")
        assert db_session.query(ExecutionLog).filter(ExecutionLog.task_id == task.id, ExecutionLog.tool_name == "file_write", ExecutionLog.event_status == "denied").count() == 1


def test_p0_tools_create_inspect_and_require_delete_approval(db_session):
    with tempfile.TemporaryDirectory() as root:
        agent, goal, task = _scope(db_session, root)
        agent.set_allowed_tools(["directory_create", "file_create", "git_status", "file_delete"])
        db_session.commit()
        executor = ToolExecutor()
        directory = asyncio.run(executor.execute(db_session, "directory_create", {"path": "pkg"}, goal.id, task.id, agent.id, "worker"))
        created = asyncio.run(executor.execute(db_session, "file_create", {"path": "pkg/value.py", "content": "value = 1\n"}, goal.id, task.id, agent.id, "worker"))
        status = asyncio.run(executor.execute(db_session, "git_status", {}, goal.id, task.id, agent.id, "worker"))
        denied = asyncio.run(executor.execute(db_session, "file_delete", {"path": "pkg/value.py"}, goal.id, task.id, agent.id, "worker"))
        approved = asyncio.run(executor.execute(db_session, "file_delete", {"path": "pkg/value.py", "approved": True}, goal.id, task.id, agent.id, "worker"))
        assert directory.status == "completed"
        assert created.status == "completed"
        assert status.status in {"completed", "failed"}  # a workspace need not be a Git repository
        assert denied.status == "denied"
        assert "approval" in (denied.error_message or "")
        assert approved.status == "completed"
        assert approved.to_dict()["result"]["tool_call_id"] == approved.id
        assert approved.to_dict()["result"]["changed_files"]


def test_workspace_state_surfaces_real_tool_evidence(db_session):
    with tempfile.TemporaryDirectory() as root:
        agent, goal, task = _scope(db_session, root)
        agent.set_allowed_tools(["file_write", "test_runner"])
        db_session.commit()
        executor = ToolExecutor()
        asyncio.run(executor.execute(db_session, "file_write", {"path": "evidence.py", "content": "value = 1\n"}, goal.id, task.id, agent.id, "worker"))
        asyncio.run(executor.execute(db_session, "test_runner", {"command": "python3 -c 'print(1)'"}, goal.id, task.id, agent.id, "worker"))
        item = get_workspace_state(db_session, goal.id)["tasks"][0]
        assert item["latest_tool_call"]["tool_name"] == "test_runner"
        assert item["test_status"] == "completed"
        assert any(path.endswith("evidence.py") for path in item["changed_files"])
        assert item["artifacts"]
