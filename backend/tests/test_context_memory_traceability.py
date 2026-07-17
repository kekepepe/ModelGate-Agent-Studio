import uuid
from datetime import datetime, timedelta, timezone

from src.models.knowledge import MemoryDraft
from src.models.workspace import Goal, Task
from src.services.context_service import build_context_package


def test_context_uses_approved_unexpired_memory_with_source_references(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Fix checkout bug", status="running")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Fix checkout", status="pending")
    usable = MemoryDraft(id=str(uuid.uuid4()), source_goal_id="prior", type="project_memory", title="Checkout fix", content="Use existing checkout validation", confidence=0.9, human_approved=True)
    usable.set_metadata({"source_references": {"goal_id": "prior", "task_ids": ["t1"], "log_ids": ["l1"], "tool_call_ids": ["c1"]}})
    expired = MemoryDraft(id=str(uuid.uuid4()), type="project_memory", title="Checkout old", content="Old rule", confidence=1.0, human_approved=True, expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    db_session.add_all([goal, task, usable, expired])
    db_session.commit()
    package = build_context_package(db_session, goal, task)
    assert [item["id"] for item in package["project_memories"]] == [usable.id]
    assert package["project_memories"][0]["source_references"]["tool_call_ids"] == ["c1"]
    assert package["source_references"][0]["memory_id"] == usable.id
