import uuid

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.model import Model
from src.models.workspace import ExecutionPlan, Goal, Task
from src.services import runtime_service
from src.services.providers.provider_factory import create_provider, set_provider


class UnhealthyProvider:
    async def health_check(self, _model):
        return {"healthy": False, "message": "provider unavailable"}


def test_runtime_stops_before_model_call_when_live_health_is_unhealthy(db_session):
    agent = AgentStation(id=str(uuid.uuid4()), name="Coder", role="coder", default_model_id="m", is_enabled=True)
    model = Model(id="m", provider="openai", model_name="m", display_name="M", is_enabled=True, api_key="test-key")
    goal = Goal(id=str(uuid.uuid4()), title="Health", status="running", execution_mode="live")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Do work", status="pending", assigned_agent_id=agent.id)
    db_session.add_all([agent, model, goal, task])
    db_session.commit()
    set_provider(UnhealthyProvider())
    try:
        result = runtime_service.execute_task_step(db_session, task.id)
    finally:
        set_provider(create_provider("mock"))
    assert result["status"] in {"failed", "handoff"}
    event = db_session.query(ExecutionLog).filter(ExecutionLog.task_id == task.id, ExecutionLog.event_type == "model_health").one()
    assert event.event_status == "failed"
    decision = db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "runtime.decision",
    ).one()
    assert decision.event_status == "replan_graph"
    assert db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal.id).count() == 2
