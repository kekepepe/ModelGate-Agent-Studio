import hashlib
import uuid

import pytest

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.workspace import Artifact, ExecutionPlan, Goal, Task
from src.services import handoff_service


def test_handoff_rejects_changed_workspace_file(db_session, tmp_path):
    source = tmp_path / "module.py"
    source.write_text("value = 1\n")
    first = AgentStation(id=str(uuid.uuid4()), name="First", role="coder", default_model_id="a", is_enabled=True)
    second = AgentStation(id=str(uuid.uuid4()), name="Second", role="coder", default_model_id="b", is_enabled=True)
    goal = Goal(id=str(uuid.uuid4()), title="Handoff", status="running", workspace_root=str(tmp_path))
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Edit", status="running", assigned_agent_id=first.id)
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    db_session.add_all([first, second, goal, task, Artifact(task_id=task.id, path=str(source), checksum=checksum)])
    db_session.commit()

    handoff = handoff_service.trigger_handoff(db_session, task.id, second.id, "b", "manual")
    source.write_text("value = 2\n")
    with pytest.raises(handoff_service.HandoffConflictError):
        handoff_service.accept_handoff(db_session, handoff["handoff_id"])


def test_handoff_conflict_api_creates_versioned_replan(client, db_session, tmp_path):
    source = tmp_path / "module.py"
    source.write_text("value = 1\n")
    first = AgentStation(id=str(uuid.uuid4()), name="First", role="coder", default_model_id="a", is_enabled=True)
    second = AgentStation(id=str(uuid.uuid4()), name="Second", role="coder", default_model_id="b", is_enabled=True)
    goal = Goal(id=str(uuid.uuid4()), title="Handoff API", status="running", workspace_root=str(tmp_path))
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Edit", status="running",
        assigned_agent_id=first.id, task_type="coding",
    )
    task.set_json("acceptance_criteria", [{"type": "diff_exists"}])
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    db_session.add_all([first, second, goal, task, Artifact(task_id=task.id, path=str(source), checksum=checksum)])
    db_session.commit()
    handoff = handoff_service.trigger_handoff(db_session, task.id, second.id, "b", "manual")
    source.write_text("value = 2\n")

    response = client.post(f"/api/v1/handoffs/{handoff['handoff_id']}/accept", json={})
    assert response.status_code == 409
    assert db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal.id).count() == 2
    decision = db_session.query(ExecutionLog).filter(
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "runtime.decision",
    ).one()
    assert decision.event_status == "replan_graph"
