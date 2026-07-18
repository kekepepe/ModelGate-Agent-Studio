import uuid

from src.models.handoff import ExecutionLog, WorkerSession
from src.models.workspace import Artifact, Goal, RuntimeRun, Task


def test_created_goal_receives_a_stable_public_run_id(client, db_session):
    response = client.post("/api/v1/goals", json={"title": "Stable workspace URL"})
    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["run_id"]
    goal = db_session.query(Goal).filter(Goal.id == payload["goal_id"]).one()
    assert goal.run_id == payload["run_id"]


def test_run_overview_and_detail_are_backed_by_persisted_state(client, db_session):
    run_id = str(uuid.uuid4())
    goal = Goal(id=str(uuid.uuid4()), run_id=run_id, title="Workspace IA", description="Unify navigation", team_preset="code-delivery", status="running", budget_tokens=1000)
    first = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Build shell", status="completed_verified", tokens_used=200)
    second = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Verify routes", status="running", assigned_agent_id="agent-a", tokens_used=100)
    worker = WorkerSession(id=str(uuid.uuid4()), goal_id=goal.id, task_id=second.id, agent_id="agent-a", model_id="model-a", status="running")
    runtime = RuntimeRun(id=run_id, goal_id=goal.id, execution_mode="mock", status="running")
    log = ExecutionLog(id=str(uuid.uuid4()), goal_id=goal.id, task_id=second.id, event_type="error", event_status="failed")
    asset = Artifact(id=str(uuid.uuid4()), run_id=run_id, task_id=first.id, type="file", path="docs/review.md", verification_status="verified")
    db_session.add_all([goal, first, second, worker, runtime, log, asset])
    db_session.commit()

    overview = client.get("/api/v1/runs?status=active&search=Workspace")
    assert overview.status_code == 200
    summary = overview.json()["data"]["items"][0]
    assert summary["run_id"] == run_id
    assert summary["progress"] == 50
    assert summary["active_agents"] == 1
    assert summary["quota_percent"] == 30
    assert summary["error_count"] == 1
    assert summary["artifact_count"] == 1

    detail = client.get(f"/api/v1/runs/{run_id}/workspace")
    assert detail.status_code == 200
    assert detail.json()["data"]["goal"]["id"] == goal.id

    assets = client.get(f"/api/v1/runs/{run_id}/assets")
    assert assets.status_code == 200
    assert assets.json()["data"]["items"][0]["path"] == "docs/review.md"

    exported = client.post(f"/api/v1/runs/{run_id}/export")
    assert exported.status_code == 200
    assert exported.json()["data"]["snapshot"] is True
    assert '"run_id":' in exported.json()["data"]["content"]
    refreshed_assets = client.get(f"/api/v1/runs/{run_id}/assets").json()["data"]["items"]
    assert any(item["type"] == "run_snapshot" for item in refreshed_assets)


def test_legacy_goal_id_resolves_as_a_run_route(client, db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Legacy bookmark", status="idle")
    db_session.add(goal)
    db_session.commit()
    response = client.get(f"/api/v1/runs/{goal.id}/workspace")
    assert response.status_code == 200
    assert response.json()["data"]["goal"]["id"] == goal.id


def test_logs_accept_run_id_context(client, db_session):
    run_id = str(uuid.uuid4())
    first = Goal(id=str(uuid.uuid4()), run_id=run_id, title="First", status="running")
    second = Goal(id=str(uuid.uuid4()), run_id=str(uuid.uuid4()), title="Second", status="running")
    db_session.add_all([
        first, second,
        ExecutionLog(id=str(uuid.uuid4()), goal_id=first.id, event_type="agent_step", event_status="completed"),
        ExecutionLog(id=str(uuid.uuid4()), goal_id=second.id, event_type="agent_step", event_status="completed"),
    ])
    db_session.commit()
    response = client.get(f"/api/v1/logs?run_id={run_id}")
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["goal_id"] == first.id
