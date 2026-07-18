import uuid
import json

from src.models.agent import AgentStation
from src.models.model import Model
from src.models.workspace import ExecutionPlan, Goal, Task
from src.models.tool import ToolCallRecord
from src.models.handoff import ExecutionLog, WorkerSession
from src.services import runtime_service
from src.services.providers.base import ModelResponse
from src.services.providers.provider_factory import create_provider, set_provider
from src.services.tool_service import seed_builtin_tools


class ScriptedProvider:
    """One deterministic Observe -> Act -> Verify model conversation."""
    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    async def generate(self, _request):
        item = self.script[self.calls]
        self.calls += 1
        return ModelResponse(content=item.get("content", ""), input_tokens=10, output_tokens=10,
                             total_tokens=20, latency_ms=0, finish_reason="tool_calls" if item.get("tool_calls") else "stop",
                             tool_calls=item.get("tool_calls"))


def _tool_call(name, arguments):
    return {"id": str(uuid.uuid4()), "function": {"name": name, "arguments": arguments}}


def _coding_task(db_session, tmp_path):
    agent = AgentStation(id=str(uuid.uuid4()), name="Coder", role="coder", default_model_id="runtime-model", is_enabled=True)
    agent.set_allowed_tools(["file_write", "test_runner"])
    model = Model(id="runtime-model", provider="mock", model_name="runtime-model", display_name="Runtime Model", is_enabled=True)
    model.set_capability_tags(["code", "reasoning", "tool_calling"])
    goal = Goal(id=str(uuid.uuid4()), title="Fix sample", status="running", execution_mode="mock", workspace_root=str(tmp_path))
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Fix and test", description="Create a fixed file and run the test", status="pending", assigned_agent_id=agent.id, task_type="coding")
    task.set_json("acceptance_criteria", [{"type": "diff_exists"}, {"type": "tests_pass"}])
    db_session.add_all([agent, model, goal, task])
    seed_builtin_tools(db_session)
    db_session.commit()
    return task


def test_agent_write_test_and_verified_completion(db_session, tmp_path):
    task = _coding_task(db_session, tmp_path)
    fixed_module = (
        "import unittest\n\n"
        "answer = 42\n\n"
        "class FixedTest(unittest.TestCase):\n"
        "    def test_answer(self):\n"
        "        self.assertEqual(answer, 42)\n"
    )
    provider = ScriptedProvider([
        {"tool_calls": [_tool_call("file_write", json.dumps({"path": "fixed.py", "content": fixed_module}))]},
        {"tool_calls": [_tool_call("test_runner", json.dumps({"command": "python3 -m unittest fixed"}))]},
        {"content": "Fixed the bug and verified the command."},
    ])
    set_provider(provider)
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))
    calls = [(item.tool_name, item.status, item.tool_output, item.error_message) for item in db_session.query(ToolCallRecord).filter(ToolCallRecord.task_id == task.id).all()]
    assert result["status"] == "completed_verified", (result["verification"], calls)
    assert [item["status"] for item in result["verification"]["results"]] == ["passed", "passed"]
    assert (tmp_path / "fixed.py").read_text() == fixed_module
    worker = db_session.query(WorkerSession).filter(WorkerSession.task_id == task.id).one()
    assert worker.step_count == 3
    assert worker.next_action == "completed"
    event_types = {
        item.event_type
        for item in db_session.query(ExecutionLog).filter(ExecutionLog.task_id == task.id).all()
    }
    assert {
        "task.assigned",
        "worker.started",
        "tool.started",
        "tool.completed",
        "artifact.created",
        "verification.started",
        "verification.passed",
        "task.completed_verified",
    }.issubset(event_types)


def test_failed_test_schedules_bounded_retry(db_session, tmp_path):
    task = _coding_task(db_session, tmp_path)
    provider = ScriptedProvider([
        {"tool_calls": [_tool_call("file_write", json.dumps({"path": "fixed.py", "content": "answer =\n"}))]},
        {"tool_calls": [_tool_call("test_runner", json.dumps({"command": "python3 -m unittest fixed"}))]},
        {"content": "The test was attempted."},
    ])
    set_provider(provider)
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))
    db_session.refresh(task)
    assert result["status"] == "pending"
    assert task.retry_count == 1
    assert task.status == "pending"
    assert task.verification_status == "failed"
    decision = db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "runtime.decision",
    ).one()
    assert decision.event_status == "revise_current_task"


def test_generic_terminal_success_cannot_satisfy_test_contract(db_session, tmp_path):
    task = _coding_task(db_session, tmp_path)
    agent = db_session.query(AgentStation).filter(AgentStation.id == task.assigned_agent_id).one()
    agent.set_allowed_tools(["file_write", "terminal_execute"])
    db_session.commit()
    provider = ScriptedProvider([
        {"tool_calls": [_tool_call("file_write", json.dumps({"path": "fixed.py", "content": "answer = 42\n"}))]},
        {"tool_calls": [_tool_call("terminal_execute", json.dumps({"command": "python3 -m unittest fixed"}))]},
        {"content": "The shell command succeeded."},
    ])
    set_provider(provider)
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))
    assert result["status"] == "pending"
    assert result["verification"]["results"][1]["status"] == "failed"


def test_exhausted_retry_restores_checkpoint_and_blocks_coding_task(db_session, tmp_path):
    original = tmp_path / "fixed.py"
    original.write_text("answer = 0\n")
    task = _coding_task(db_session, tmp_path)
    db_session.query(Goal).filter(Goal.id == task.goal_id).update({"execution_mode": "sandbox"})
    task.max_retries = 0
    db_session.commit()
    provider = ScriptedProvider([
        {"tool_calls": [_tool_call("file_write", json.dumps({"path": "fixed.py", "content": "answer = 42\n"}))]},
        {"content": "I changed the file but cannot provide successful test evidence."},
    ])
    set_provider(provider)
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))
    db_session.refresh(task)
    assert result["status"] == "blocked"
    assert task.status == "blocked"
    assert "restored latest checkpoints" in (task.blocked_reason or "")
    assert original.read_text() == "answer = 0\n"
    plans = db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == task.goal_id).order_by(ExecutionPlan.version).all()
    assert [plan.version for plan in plans] == [1, 2]
    replacement = db_session.query(Task).filter(Task.parent_task_id == task.id).one()
    assert replacement.status == "pending"
    decision = db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "runtime.decision",
    ).one()
    assert decision.event_status == "replan_graph"
