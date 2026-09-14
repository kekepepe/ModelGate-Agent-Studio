"""V1.1: LLM-generated handoff summaries.

trigger_handoff must try the from-station model first (live mode), record
provenance (generated_by / generated_at), and fall back to the deterministic
template whenever the LLM path is unavailable — mock mode, missing model
record, provider failure, or unparseable output.
"""
import json
import uuid

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.model import Model
from src.models.quota import QuotaRecord
from src.models.workspace import Goal, Task
from src.services import handoff_service
from src.services.providers import set_provider
from src.services.providers.base import ModelResponse
from src.services.providers.provider_factory import create_provider


class _StubProvider:
    """Minimal ModelProvider double that answers generate() with fixed text."""

    def __init__(self, content: str):
        self.content = content
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        return ModelResponse(
            content=self.content,
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            latency_ms=5,
        )


def _make_station(name, model_id):
    return AgentStation(
        id=str(uuid.uuid4()), name=name, role="coder",
        default_model_id=model_id, is_enabled=True,
    )


def _make_task_fixture(db_session, *, execution_mode, model=None):
    first = _make_station("Coder One", model.id if model else "model-missing")
    second = _make_station("Coder Two", "model-target")
    goal = Goal(
        id=str(uuid.uuid4()), title="Handoff Summary Goal", status="running",
        execution_mode=execution_mode,
    )
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Edit module",
        description="Refactor the parser module", status="running",
        assigned_agent_id=first.id,
    )
    task.set_json("acceptance_criteria", [{"type": "diff_exists"}])
    rows = [first, second, goal, task]
    if model is not None:
        rows.append(model)
    db_session.add_all(rows)
    db_session.commit()
    return first, second, goal, task


def _llm_payload():
    return {
        "original_goal": "Ship the parser refactor",
        "current_task": "Refactor the parser module",
        "completed_work": ["Wrote the tokenizer"],
        "unfinished_work": ["Wire the AST builder"],
        "important_constraints": ["Keep the public API stable"],
        "key_decisions": ["Chose recursive descent"],
        "errors_and_risks": ["Tokenizer has a known edge case"],
        "next_suggested_steps": ["Run the parser suite"],
        "context_needed": ["See artifacts"],
        "changed_files": [],
        "tool_results": [],
        "verification_state": [],
        "workspace_checkpoint": "",
        "recommended_next_action": "Continue wiring the AST builder",
    }


def test_mock_mode_skips_llm_and_uses_fallback(db_session):
    model = Model(
        id="model-mock-src", provider="openai", model_name="gpt-mock",
        display_name="GPT Mock", is_enabled=True, api_key="sk-test",
    )
    first, second, goal, task = _make_task_fixture(db_session, execution_mode="mock", model=model)
    stub = _StubProvider(json.dumps(_llm_payload()))
    set_provider(stub)

    result = handoff_service.trigger_handoff(db_session, task.id, second.id, second.default_model_id, "error", "boom")

    assert result["status"] == "ready"
    stored = handoff_service.get_handoff(db_session, result["handoff_id"])
    summary = stored["handoff_summary"]
    assert summary["generated_by"] == "fallback"
    assert summary["generated_at"]
    assert stub.requests == []  # mock mode never calls the provider


def test_llm_summary_generated_via_provider(db_session):
    model = Model(
        id="model-llm-src", provider="openai", model_name="gpt-llm",
        display_name="GPT LLM", is_enabled=True, api_key="sk-test",
    )
    first, second, goal, task = _make_task_fixture(db_session, execution_mode="live", model=model)
    stub = _StubProvider(json.dumps(_llm_payload()))
    set_provider(stub)

    result = handoff_service.trigger_handoff(db_session, task.id, second.id, second.default_model_id, "quality_issue", "verification failed")

    assert result["status"] == "ready"
    assert len(stub.requests) == 1
    request = stub.requests[0]
    assert request.model == "gpt-llm"
    assert request.messages[0]["role"] == "system"
    user_payload = json.loads(request.messages[1]["content"])
    assert user_payload["current_task"] == "Refactor the parser module"
    assert user_payload["handoff_reason"] == "quality_issue"

    stored = handoff_service.get_handoff(db_session, result["handoff_id"])
    summary = stored["handoff_summary"]
    assert summary["generated_by"] == "llm"
    assert summary["generated_at"]
    assert summary["original_goal"] == "Ship the parser refactor"
    assert summary["recommended_next_action"] == "Continue wiring the AST builder"

    # Usage is recorded against the source model and the provenance is logged.
    quota = db_session.query(QuotaRecord).filter(QuotaRecord.model_id == model.id).one()
    assert quota.total_tokens == 300
    log = db_session.query(ExecutionLog).filter(
        ExecutionLog.handoff_id == result["handoff_id"],
        ExecutionLog.event_type == "model_call",
    ).one()
    assert log.get_metadata()["generated_by"] == "llm"


def test_unparseable_llm_answer_falls_back(db_session):
    model = Model(
        id="model-garbage", provider="openai", model_name="gpt-garbage",
        display_name="GPT Garbage", is_enabled=True, api_key="sk-test",
    )
    first, second, goal, task = _make_task_fixture(db_session, execution_mode="live", model=model)
    set_provider(_StubProvider("I could not produce JSON today, sorry."))

    result = handoff_service.trigger_handoff(db_session, task.id, second.id, second.default_model_id, "manual")

    stored = handoff_service.get_handoff(db_session, result["handoff_id"])
    summary = stored["handoff_summary"]
    assert summary["generated_by"] == "fallback"
    assert summary["original_goal"] == "Handoff Summary Goal"
    assert summary["current_task"] == "Refactor the parser module"


def test_missing_model_record_falls_back_without_provider_call(db_session):
    first, second, goal, task = _make_task_fixture(db_session, execution_mode="live", model=None)
    stub = _StubProvider(json.dumps(_llm_payload()))
    set_provider(stub)

    result = handoff_service.trigger_handoff(db_session, task.id, second.id, second.default_model_id, "manual")

    assert stub.requests == []
    stored = handoff_service.get_handoff(db_session, result["handoff_id"])
    assert stored["handoff_summary"]["generated_by"] == "fallback"


def test_provider_exception_falls_back(db_session):
    model = Model(
        id="model-exploding", provider="openai", model_name="gpt-boom",
        display_name="GPT Boom", is_enabled=True, api_key="sk-test",
    )
    first, second, goal, task = _make_task_fixture(db_session, execution_mode="live", model=model)

    class _ExplodingProvider(_StubProvider):
        async def generate(self, request):
            raise RuntimeError("provider down")

    set_provider(_ExplodingProvider(""))

    result = handoff_service.trigger_handoff(db_session, task.id, second.id, second.default_model_id, "error", "upstream down")
    stored = handoff_service.get_handoff(db_session, result["handoff_id"])
    assert stored["handoff_summary"]["generated_by"] == "fallback"


def test_conftest_provider_restored():
    # Guard that the suite-level mock provider is back in place after the
    # stubs installed above (conftest also resets per test; this documents it).
    from src.services.providers.provider_factory import get_provider

    assert get_provider() is not None
    set_provider(create_provider("mock"))
