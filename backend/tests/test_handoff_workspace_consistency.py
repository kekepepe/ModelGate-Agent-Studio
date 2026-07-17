import hashlib
import uuid

import pytest

from src.models.agent import AgentStation
from src.models.workspace import Artifact, Goal, Task
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
