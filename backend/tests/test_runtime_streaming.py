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
