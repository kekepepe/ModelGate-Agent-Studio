"""V1.5 QL5: LLM-first memory distillation with rule fallback.

Live goals ask the planner's model to distill the run evidence into
dense reusable knowledge; mock goals (or any LLM failure) keep the
rule template — provenance recorded as generated_by in the reason.
"""
import json
import uuid

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.model import Model
from src.models.workspace import Goal, Task
from src.services.curator_service import generate_memories
from src.services.providers.base import ModelResponse
from src.services.providers.provider_factory import set_provider


class _StubProvider:
    def __init__(self, content):
        self.content = content
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        return ModelResponse(content=self.content, input_tokens=10, output_tokens=10,
                             total_tokens=20, latency_ms=1)


def _completed_goal(db_session, *, execution_mode):
    goal = Goal(id=str(uuid.uuid4()), title="Distill goal", status="completed", execution_mode=execution_mode)
    planner = AgentStation(id=str(uuid.uuid4()), name="Planner", role="planner",
                           default_model_id="model-distill", is_enabled=True)
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Do the work", status="completed_verified",
                assigned_agent_id=planner.id)
    log = ExecutionLog(goal_id=goal.id, task_id=task.id, agent_id=planner.id,
                       event_type="model_call", event_status="completed")
    db_session.add_all([planner, goal, task, log])
    db_session.commit()
    return goal, planner


def _planner_model(db_session):
    model = Model(id="model-distill", provider="openai", model_name="gpt-distill",
                  display_name="Distill", is_enabled=True, api_key="sk-test")
    db_session.merge(model)
    db_session.commit()
    return model


def test_live_goal_distills_via_llm(db_session):
    goal, _planner = _completed_goal(db_session, execution_mode="live")
    _planner_model(db_session)
    payload = json.dumps({"title": "t", "content": "Dense reusable guidance: always seed the DB before e2e."})
    stub = _StubProvider(payload)
    set_provider(stub)

    summary = generate_memories(db_session, goal.id, run_id="run-llm")

    assert summary["total_memories"] >= 1
    assert len(stub.requests) == 1
    memory = next(m for m in summary["memory_drafts"] if m["type"] == "project_memory")
    assert "seed the DB" in memory["content"]
    assert "(llm)" in memory["reason"]


def test_mock_goal_keeps_rule_template(db_session):
    goal, _planner = _completed_goal(db_session, execution_mode="mock")
    _planner_model(db_session)
    stub = _StubProvider(json.dumps({"title": "t", "content": "should not be used"}))
    set_provider(stub)

    summary = generate_memories(db_session, goal.id, run_id="run-rule")

    assert len(stub.requests) == 0, "mock mode never calls the provider"
    memory = next(m for m in summary["memory_drafts"] if m["type"] == "project_memory")
    assert "Goal:" in memory["content"], "rule template content"
    assert "(rule)" in memory["reason"]


def test_unparseable_llm_answer_falls_back_to_rule(db_session):
    goal, _planner = _completed_goal(db_session, execution_mode="live")
    _planner_model(db_session)
    set_provider(_StubProvider("no json here, sorry"))

    summary = generate_memories(db_session, goal.id, run_id="run-fallback")

    memory = next(m for m in summary["memory_drafts"] if m["type"] == "project_memory")
    assert "Goal:" in memory["content"]
    assert "(rule)" in memory["reason"]
