import uuid

from src.models.workspace import Goal, Task
from src.services import task_service


def _task(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Graph controls", status="running", execution_mode="mock")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Implement", status="blocked", task_type="coding", priority=10)
    task.set_json("required_tools", ["file_read", "file_write"])
    db_session.add_all([goal, task])
    db_session.commit()
    return task


def test_retry_and_cancel_task(db_session):
    task = _task(db_session)
    retried = task_service.retry_task(db_session, task.id)
    assert retried["status"] == "pending"
    cancelled = task_service.cancel_task(db_session, task.id, "No longer needed")
    assert cancelled["status"] == "cancelled"
    assert cancelled["blocked_reason"] == "No longer needed"


def test_split_task_creates_child_graph_nodes(db_session):
    task = _task(db_session)
    children = task_service.split_task(db_session, task.id, ["Inspect backend", "Implement backend"])
    assert [child["title"] for child in children] == ["Inspect backend", "Implement backend"]
    assert all(child["parent_task_id"] == task.id for child in children)
    assert all(child["required_tools"] == ["file_read", "file_write"] for child in children)
    db_session.refresh(task)
    assert task.status == "cancelled"
