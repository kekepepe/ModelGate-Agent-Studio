import uuid

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.model import Model
from src.models.workspace import Goal, Task
from src.services import runtime_service
from src.services.providers.base import ModelStreamEvent
from src.services.providers.provider_factory import create_provider, set_provider


class StreamingProvider:
    async def health_check(self, _model):
        return {"healthy": True}

    async def stream(self, _request):
        yield ModelStreamEvent(type="token", content="Hello ", request_id="req-stream")
        yield ModelStreamEvent(type="token", content="world", request_id="req-stream")
        yield ModelStreamEvent(type="done", request_id="req-stream")

    async def generate(self, _request):
        raise AssertionError("Tool-free live task should use stream")


def test_tool_free_live_task_persists_real_stream_chunks(db_session):
    agent = AgentStation(id=str(uuid.uuid4()), name="Answer", role="summarizer", default_model_id="m", is_enabled=True)
    model = Model(id="m", provider="openai", model_name="m", display_name="M", is_enabled=True, api_key="key")
    goal = Goal(id=str(uuid.uuid4()), title="Answer", status="running", execution_mode="live")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Answer", status="pending", assigned_agent_id=agent.id, task_type="direct")
    db_session.add_all([agent, model, goal, task])
    db_session.commit()
    set_provider(StreamingProvider())
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))
    assert result["output"] == "Hello world"
    chunks = db_session.query(ExecutionLog).filter(ExecutionLog.task_id == task.id, ExecutionLog.event_type == "model_stream").all()
    assert [chunk.output_summary for chunk in chunks] == ["Hello ", "world"]
    streaming = db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "model.streaming",
    ).order_by(ExecutionLog.created_at.asc()).all()
    assert [item.event_status for item in streaming] == ["started", "completed"]


class ToolStreamingProvider:
    def __init__(self):
        self.call_count = 0

    async def health_check(self, _model):
        return {"healthy": True}

    async def stream(self, request):
        self.call_count += 1
        if self.call_count == 1:
            yield ModelStreamEvent(
                type="tool_call_delta",
                request_id="req-tool-stream",
                raw={
                    "choices": [{
                        "delta": {"tool_calls": [{
                            "index": 0,
                            "id": "call-1",
                            "type": "function",
                            "function": {"name": "workspace_list", "arguments": "{}"},
                        }]},
                        "finish_reason": "tool_calls",
                    }],
                },
            )
            yield ModelStreamEvent(
                type="done", request_id="req-tool-stream",
                raw={"usage": {"prompt_tokens": 4, "completion_tokens": 1, "total_tokens": 5}, "finish_reason": "tool_calls"},
            )
        else:
            yield ModelStreamEvent(type="token", content="done", request_id="req-tool-stream")
            yield ModelStreamEvent(
                type="done", request_id="req-tool-stream",
                raw={"usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6}, "finish_reason": "stop"},
            )

    async def generate(self, _request):
        raise AssertionError("Tool-enabled live task should also use stream")


def test_tool_enabled_live_task_reconstructs_streaming_tool_call(db_session, tmp_path):
    agent = AgentStation(id=str(uuid.uuid4()), name="Answer", role="summarizer", default_model_id="m2", is_enabled=True)
    agent.set_allowed_tools(["workspace_list"])
    model = Model(id="m2", provider="openai", model_name="m2", display_name="M2", is_enabled=True, api_key="key")
    goal = Goal(
        id=str(uuid.uuid4()), title="Answer", status="running", execution_mode="live",
        workspace_root=str(tmp_path),
    )
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Answer", status="pending",
        assigned_agent_id=agent.id, task_type="direct",
    )
    db_session.add_all([agent, model, goal, task])
    db_session.commit()
    provider = ToolStreamingProvider()
    set_provider(provider)
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))
    assert result["output"] == "done"
    assert result["tool_call_count"] == 1
    streaming = db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "model.streaming",
        ExecutionLog.event_status == "completed",
    ).all()
    assert len(streaming) == 2
