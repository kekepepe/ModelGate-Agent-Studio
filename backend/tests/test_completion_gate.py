import uuid

from src.models.handoff import ExecutionLog
from src.models.tool import ToolCallRecord
from src.models.workspace import Artifact, Goal, Task, VerificationResult
from src.services import verifier_service


def _goal_task(db_session, *, task_type="direct", risk_level="low", status="running", output="done"):
    goal = Goal(id=str(uuid.uuid4()), title="Completion gate", status="running", execution_mode="mock")
    task = Task(
        id=str(uuid.uuid4()),
        goal_id=goal.id,
        title="Prove completion",
        status=status,
        task_type=task_type,
        risk_level=risk_level,
        output=output,
    )
    db_session.add_all([goal, task])
    db_session.commit()
    return goal, task


def test_command_exit_code_and_user_approval_complete_contract(db_session):
    goal, task = _goal_task(db_session)
    task.set_json("acceptance_criteria", [
        {"type": "command_exit_code", "tool": "terminal_execute", "command": "check", "exit_code": 7},
        {"type": "user_approval"},
    ])
    call = ToolCallRecord(
        id=str(uuid.uuid4()),
        goal_id=goal.id,
        task_id=task.id,
        agent_id="agent",
        worker_id="worker",
        tool_name="terminal_execute",
        status="failed",
    )
    call.set_tool_input({"command": "check"})
    call.set_result({"exit_code": 7, "status": "failed"})
    approval = ExecutionLog(
        goal_id=goal.id,
        task_id=task.id,
        event_type="task.approved",
        event_status="completed",
    )
    db_session.add_all([call, approval])
    db_session.commit()

    verification = verifier_service.verify_task_contract(db_session, task)
    task.status = "completed_verified"
    task.verification_status = verification["status"]
    db_session.commit()
    gate = verifier_service.evaluate_goal_completion(db_session, goal, emit_event=False)

    assert verification["status"] == "passed"
    assert [item["exit_code"] for item in verification["results"]] == [7, 0]
    assert gate["allowed"] is True
    assert gate["status"] == "passed"


def test_code_completion_claim_without_artifact_or_results_is_rejected(db_session):
    goal, task = _goal_task(
        db_session,
        task_type="coding",
        status="completed_verified",
        output="I completed the change.",
    )
    task.verification_status = "passed"
    task.set_json("acceptance_criteria", [{"type": "diff_exists"}])
    db_session.commit()

    gate = verifier_service.evaluate_goal_completion(db_session, goal, emit_event=False)

    assert gate["allowed"] is False
    assert gate["goal_status"] == "revision_required"
    assert "Missing VerificationResult" in " ".join(gate["tasks"][0]["reasons"])
    assert "no tracked Artifact" in " ".join(gate["tasks"][0]["reasons"])


def test_verified_code_contract_marks_artifact_verified(db_session):
    goal, task = _goal_task(db_session, task_type="coding")
    task.set_json("acceptance_criteria", [{"type": "diff_exists"}])
    artifact = Artifact(task_id=task.id, type="file", path="changed.py", checksum="abc", verification_status="unverified")
    db_session.add(artifact)
    db_session.commit()

    verification = verifier_service.verify_task_contract(db_session, task)
    task.status = "completed_verified"
    task.verification_status = verification["status"]
    db_session.commit()
    gate = verifier_service.evaluate_goal_completion(db_session, goal, emit_event=False)

    db_session.refresh(artifact)
    assert artifact.verification_status == "verified"
    assert gate["allowed"] is True
    assert gate["status"] == "passed"


def test_unresolved_high_risk_task_cannot_complete_goal(db_session):
    goal, task = _goal_task(
        db_session,
        risk_level="high",
        status="completed_unverified",
        output="Subjective result",
    )
    blocked = verifier_service.evaluate_goal_completion(db_session, goal, emit_event=False)
    assert blocked["goal_status"] == "revision_required"

    db_session.add(ExecutionLog(
        goal_id=goal.id,
        task_id=task.id,
        event_type="task.approved",
        event_status="completed",
    ))
    db_session.commit()
    approved = verifier_service.evaluate_goal_completion(db_session, goal, emit_event=False)
    assert approved["allowed"] is True
    assert approved["status"] == "unverified"


def test_verified_downstream_reviewer_resolves_transitive_high_risk_gate(db_session):
    goal, risky = _goal_task(
        db_session,
        risk_level="high",
        status="completed_unverified",
        output="Risky result",
    )
    middle = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Package result",
        status="completed_unverified", task_type="direct", output="Packaged",
    )
    middle.set_json("dependencies", [risky.id])
    reviewer = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Independent review",
        status="completed_verified", task_type="verification", output="Approved",
        verification_status="passed",
    )
    reviewer.set_json("dependencies", [middle.id])
    reviewer.set_json("acceptance_criteria", [{"type": "review_score", "minimum": 0.8}])
    result = VerificationResult(
        task_id=reviewer.id,
        criterion_type="review_score",
        command_or_rule="supervisor_review",
        status="passed",
        evidence="Independent review passed",
        exit_code=0,
    )
    db_session.add_all([middle, reviewer, result])
    db_session.commit()

    gate = verifier_service.evaluate_goal_completion(db_session, goal, emit_event=False)

    assert gate["allowed"] is True
    assert gate["status"] == "unverified"
