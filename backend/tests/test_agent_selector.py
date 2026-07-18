import uuid

from src.models.agent import AgentStation
from src.models.model import Model
from src.models.quota import QuotaRecord
from src.models.selection import AgentSelectionDecision
from src.models.workspace import Task


def _model(model_id: str, *, cost: int = 2, speed: int = 2):
    model = Model(
        id=model_id, provider="mock", model_name=model_id, display_name=model_id,
        max_context_tokens=131072, cost_level=cost, speed_level=speed, is_enabled=True,
    )
    model.set_capability_tags(["code", "reasoning", "tool_calling"])
    return model


def _agent(agent_id: str, model_id: str, proficiency: float, tools=None, scopes=None):
    agent = AgentStation(
        id=agent_id, name=agent_id, role="coder", default_model_id=model_id,
        is_enabled=True, max_concurrency=1, allow_handoff=True,
        total_tasks_completed=8, total_tasks_failed=2,
    )
    agent.set_capability_profile({"code_read": proficiency, "code_edit": proficiency, "test": proficiency})
    agent.set_allowed_tools(tools or [])
    agent.set_workspace_permissions(scopes or [])
    agent.set_input_types(["text"]); agent.set_output_types(["text"])
    return agent


def test_joint_selector_records_candidates_eliminations_model_and_fallback(client, db_session):
    primary = _model("code-primary")
    backup = _model("code-backup", cost=3)
    winner = _agent("winner", primary.id, .95, ["file_read", "file_write"], ["frontend/**"])
    winner.set_backup_model_ids([backup.id])
    missing_tool = _agent("missing-tool", primary.id, 1.0, ["file_read"], ["frontend/**"])
    wrong_scope = _agent("wrong-scope", primary.id, 1.0, ["file_read", "file_write"], ["backend/**"])
    db_session.add_all([primary, backup, winner, missing_tool, wrong_scope]); db_session.commit()

    response = client.post("/api/v1/router/select-agent", json={
        "goal_id": "goal-selector", "task_id": "task-selector", "task_type": "coding",
        "required_capabilities": ["code_edit"], "required_tools": ["file_read", "file_write"],
        "workspace_scope": "frontend/**", "context_length_estimate": 4000,
    })
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["selected_agent_id"] == winner.id
    assert result["selected_model_id"] == primary.id
    assert result["backup_model_ids"] == [backup.id]
    by_id = {item["agent_id"]: item for item in result["candidates"]}
    assert "missing tools" in by_id[missing_tool.id]["elimination_reasons"][0]
    assert "workspace scope" in by_id[wrong_scope.id]["elimination_reasons"][0]
    assert set(by_id[winner.id]["score_breakdown"]) >= {"capability_match", "model_fit", "quota_fit", "load_fit"}
    assert result["fallback_entry"]["handoff_allowed"] is True
    decision = db_session.query(AgentSelectionDecision).one()
    assert decision.task_id == "task-selector" and decision.selected_agent_id == winner.id
    assert client.get("/api/v1/goals/goal-selector/selection-decisions").json()["data"][0]["id"] == decision.id


def test_selector_eliminates_quota_blocked_models_and_loaded_agents(client, db_session):
    blocked_model = _model("blocked-model")
    blocked = _agent("blocked-agent", blocked_model.id, 1.0, ["file_read"])
    db_session.add_all([
        blocked_model, blocked,
        QuotaRecord(id=str(uuid.uuid4()), provider="mock", model_id=blocked_model.id,
                    model_name=blocked_model.model_name, quota_status="cooldown"),
        Task(id="active-task", goal_id="other", title="Busy", status="running", assigned_agent_id=blocked.id),
    ]); db_session.commit()

    response = client.post("/api/v1/router/select-agent", json={
        "task_id": "new-task", "required_capabilities": ["code_read"], "required_tools": ["file_read"],
    })
    assert response.status_code == 503
    message = response.json()["detail"]["error"]["message"]
    assert "concurrency limit reached" in message
    assert "no enabled model" in message


def test_capability_registry_exposes_explicit_operating_policy(client, db_session):
    model = _model("registry-model")
    agent = _agent("registry-agent", model.id, .8, ["file_read"], ["docs/**"])
    agent.max_tokens_per_task = 12000
    agent.max_steps_per_task = 6
    agent.max_consecutive_failures = 2
    db_session.add_all([model, agent]); db_session.commit()

    payload = client.get("/api/v1/capabilities").json()["data"]
    record = payload["agents"][0]
    assert "code_edit" in payload["available_capabilities"]
    assert record["capabilities"]["code_edit"] == .8
    assert record["workspace_permissions"] == ["docs/**"]
    assert record["limits"] == {"max_concurrency": 1, "max_tokens": 12000, "max_steps": 6, "max_failures": 2}
