import json
import uuid
from datetime import datetime, timedelta, timezone

from src.models.agent import AgentStation
from src.models.model import Model
from src.models.tool import ToolCallRecord
from src.models.workspace import Goal, Task
from src.models.workspace import RuntimeRun
from src.services import runtime_service
from src.services.providers.base import ModelResponse
from src.services.providers.provider_factory import create_provider, set_provider
from src.services.tool_service import seed_builtin_tools


class RepeatingProvider:
    async def generate(self, _request):
        tool_call = {"id": str(uuid.uuid4()), "function": {"name": "file_read", "arguments": json.dumps({"path": "value.txt"})}}
        return ModelResponse(content="", input_tokens=1, output_tokens=1, total_tokens=2, latency_ms=0, finish_reason="tool_calls", tool_calls=[tool_call])


class TokenHeavyProvider:
    async def generate(self, _request):
        return ModelResponse(content="done", input_tokens=2, output_tokens=2, total_tokens=4, latency_ms=0)


def test_resource_limit_reports_token_and_duration_boundaries():
    agent = AgentStation(
        name="Bounded", role="coder", default_model_id="m",
        max_tokens_per_task=10, max_duration_seconds=5,
    )
    assert "token budget exceeded" in runtime_service._resource_limit_error(agent, 11, 0)
    assert "duration budget exceeded" in runtime_service._resource_limit_error(agent, 0, __import__("time").time() - 6)


def test_runtime_stops_when_agent_token_budget_is_exceeded(db_session, tmp_path):
    agent = AgentStation(
        id=str(uuid.uuid4()), name="Bounded", role="coder", default_model_id="m", is_enabled=True,
        max_steps_per_task=2, max_tool_calls_per_task=2, max_tokens_per_task=3,
    )
    model = Model(id="m", provider="mock", model_name="m", display_name="M", is_enabled=True)
    goal = Goal(id=str(uuid.uuid4()), title="Bound", status="running", execution_mode="mock", workspace_root=str(tmp_path))
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Bounded call", status="pending", assigned_agent_id=agent.id)
    db_session.add_all([agent, model, goal, task])
    db_session.commit()
    set_provider(TokenHeavyProvider())
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))
    assert result["status"] == "failed"
    stored_task = db_session.query(Task).filter(Task.id == task.id).one()
    assert stored_task.status == "failed"


def test_run_budget_guard_blocks_new_work_after_token_or_time_limit(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Bounded run", status="running", budget_tokens=10, max_duration_seconds=60)
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Prior task", status="completed", tokens_used=10)
    run = RuntimeRun(id=str(uuid.uuid4()), goal_id=goal.id, execution_mode="mock", budget_tokens=10, max_duration_seconds=60)
    db_session.add_all([goal, task, run])
    db_session.commit()
    assert "token budget exhausted" in runtime_service._run_resource_limit_error(db_session, run)
    task.tokens_used = 0
    run.started_at = datetime.now(timezone.utc) - timedelta(seconds=61)
    db_session.commit()
    assert "duration budget exhausted" in runtime_service._run_resource_limit_error(db_session, run)


def test_identical_tool_call_is_not_executed_twice(db_session, tmp_path):
    (tmp_path / "value.txt").write_text("value\n")
    agent = AgentStation(id=str(uuid.uuid4()), name="Coder", role="coder", default_model_id="m", is_enabled=True, max_steps_per_task=5, max_tool_calls_per_task=5)
    agent.set_allowed_tools(["file_read"])
    model = Model(id="m", provider="mock", model_name="m", display_name="M", is_enabled=True)
    goal = Goal(id=str(uuid.uuid4()), title="Guard", status="running", execution_mode="mock", workspace_root=str(tmp_path))
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Read once", status="pending", assigned_agent_id=agent.id)
    db_session.add_all([agent, model, goal, task])
    seed_builtin_tools(db_session)
    db_session.commit()
    set_provider(RepeatingProvider())
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))
    calls = db_session.query(ToolCallRecord).filter(ToolCallRecord.task_id == task.id, ToolCallRecord.tool_name == "file_read").count()
    assert calls == 1
    assert result["status"] in {"failed", "handoff"}
