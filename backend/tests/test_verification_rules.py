import uuid

from src.models.tool import ToolCallRecord
from src.models.workspace import Goal, Task
from src.services import runtime_service


def _task(db_session, criteria):
    goal = Goal(id=str(uuid.uuid4()), title="Verify", status="running", execution_mode="mock")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Check", status="running", task_type="coding")
    task.set_json("acceptance_criteria", criteria)
    db_session.add_all([goal, task])
    db_session.commit()
    return task


def _success_call(task, tool_name):
    return ToolCallRecord(id=str(uuid.uuid4()), goal_id=task.goal_id, task_id=task.id, agent_id="a", worker_id="w", tool_name=tool_name, status="completed", tool_output="ok")


def test_named_verification_tools_satisfy_their_matching_contracts(db_session):
    task = _task(db_session, [{"type": "lint_pass"}, {"type": "typecheck_pass"}, {"type": "build_pass"}])
    db_session.add_all([_success_call(task, "lint_run"), _success_call(task, "typecheck_run"), _success_call(task, "build_run")])
    db_session.commit()
    result = runtime_service._verify_task(db_session, task)
    assert result["status"] == "passed"


def test_wrong_verification_tool_cannot_satisfy_contract(db_session):
    task = _task(db_session, [{"type": "lint_pass"}])
    db_session.add(_success_call(task, "test_runner"))
    db_session.commit()
    result = runtime_service._verify_task(db_session, task)
    assert result["status"] == "failed"
