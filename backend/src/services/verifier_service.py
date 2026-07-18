"""Evidence-backed Task verification and Goal completion gates."""

import os
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from src.models.handoff import ExecutionLog
from src.models.supervisor import SupervisorReview
from src.models.tool import ToolCallRecord
from src.models.workspace import Artifact, Goal, Task, VerificationResult
from src.services import log_service


WRITE_TOOLS = {"file_create", "file_write", "file_patch", "directory_create"}
DETERMINISTIC_TASK_TYPES = {"coding", "merge", "verification"}
SUCCESS_STATUSES = {"completed", "completed_verified", "completed_unverified", "skipped"}
FAILURE_STATUSES = {"failed", "blocked", "cancelled", "revision_required"}


def verify_task_contract(db: Session, task: Task) -> Dict[str, Any]:
    """Evaluate one persisted Completion Contract and retain every result."""
    criteria = task._get_json("acceptance_criteria")
    if not criteria:
        return {"status": "unverified", "results": []}

    artifacts = _relevant_artifacts(db, task)
    own_artifacts = db.query(Artifact).filter(Artifact.task_id == task.id).all()
    latest_change = max((item.created_at for item in own_artifacts), default=None)
    results: List[Dict[str, Any]] = []
    all_passed = True
    for criterion in criteria:
        kind = criterion.get("type") if isinstance(criterion, dict) else "unknown"
        passed, evidence, command, exit_code = _evaluate_criterion(
            db,
            task,
            criterion if isinstance(criterion, dict) else {},
            kind,
            artifacts,
            latest_change,
        )
        result = VerificationResult(
            task_id=task.id,
            criterion_type=kind,
            command_or_rule=command,
            status="passed" if passed else "failed",
            evidence=evidence,
            exit_code=exit_code,
        )
        db.add(result)
        results.append({
            "type": kind,
            "status": result.status,
            "evidence": evidence,
            "command_or_rule": command,
            "exit_code": exit_code,
        })
        all_passed = all_passed and passed

    if all_passed:
        for artifact in artifacts:
            artifact.verification_status = "verified"
    return {"status": "passed" if all_passed else "failed", "results": results}


def evaluate_goal_completion(db: Session, goal: Goal, *, emit_event: bool = True) -> Dict[str, Any]:
    """Decide whether the active Plan has enough evidence to complete a Goal."""
    from src.services import replan_service

    tasks = replan_service.get_active_runtime_tasks(db, goal.id)
    task_evidence = [_task_gate_evidence(db, task, tasks) for task in tasks]
    failures = [item for item in task_evidence if not item["satisfied"]]
    waiting = [task for task in tasks if task.status == "waiting_approval"]
    unfinished = [
        task for task in tasks
        if task.status not in SUCCESS_STATUSES | FAILURE_STATUSES | {"waiting_approval"}
    ]
    hard_failures = [task for task in tasks if task.status in FAILURE_STATUSES]

    if not tasks:
        allowed, gate_status, goal_status = False, "failed", "blocked"
        reason = "Goal has no active Task graph to verify."
    elif waiting:
        allowed, gate_status, goal_status = False, "pending", "waiting_approval"
        reason = "Human approval is still required."
    elif unfinished:
        allowed, gate_status, goal_status = False, "pending", "blocked"
        reason = "Active Plan still contains unfinished Tasks."
    elif hard_failures:
        allowed, gate_status, goal_status = False, "failed", "revision_required"
        reason = "One or more required Tasks ended unsuccessfully."
    elif failures:
        allowed, gate_status, goal_status = False, "failed", "revision_required"
        reason = "Completion evidence is missing or failed."
    else:
        deterministic = [item for item in task_evidence if item["verification_required"]]
        allowed, goal_status = True, "completed"
        gate_status = "passed" if len(deterministic) == len(task_evidence) else "unverified"
        reason = (
            "All active Tasks passed deterministic Completion Contracts."
            if gate_status == "passed"
            else "All active Tasks reached valid terminal states; subjective Tasks remain explicitly unverified."
        )

    bundle = {
        "allowed": allowed,
        "status": gate_status,
        "goal_status": goal_status,
        "reason": reason,
        "tasks": task_evidence,
        "failed_task_ids": [item["task_id"] for item in failures],
    }
    if emit_event:
        log_service.create_log(db, {
            "goal_id": goal.id,
            "event_type": "goal.completion_gate",
            "event_status": "approved" if allowed else "needs_revision" if goal_status == "revision_required" else "blocked",
            "output_summary": reason,
            "metadata": {
                "allowed": allowed,
                "verification_status": gate_status,
                "goal_status": goal_status,
                "failed_task_ids": bundle["failed_task_ids"],
            },
        })
    return bundle


def _evaluate_criterion(
    db: Session,
    task: Task,
    criterion: Dict[str, Any],
    kind: str,
    artifacts: List[Artifact],
    latest_change,
) -> tuple[bool, str, str, Optional[int]]:
    if kind == "diff_exists":
        passed = bool(artifacts)
        return passed, f"{len(artifacts)} tracked changed file(s)", "artifact_register", 0 if passed else 1

    if kind == "file_exists":
        goal = db.query(Goal).filter(Goal.id == task.goal_id).one()
        root = os.path.realpath(goal.workspace_root or ".")
        target = os.path.realpath(os.path.join(root, criterion.get("target", "")))
        try:
            in_scope = os.path.commonpath([root, target]) == root
        except ValueError:
            in_scope = False
        passed = in_scope and os.path.isfile(target)
        return passed, target, "file_exists", 0 if passed else 1

    named_tools = {
        "tests_pass": "test_runner",
        "lint_pass": "lint_run",
        "typecheck_pass": "typecheck_run",
        "build_pass": "build_run",
    }
    if kind in named_tools:
        required_tool = named_tools[kind]
        call = _latest_tool_call(db, task.id, required_tool, latest_change=latest_change, successful_only=True)
        evidence = (
            (call.tool_output or "")[:1000]
            if call
            else f"No successful {required_tool} command after the latest change"
        )
        command = call.get_tool_input().get("command", required_tool) if call else required_tool
        return call is not None, evidence, command, 0 if call else 1

    if kind == "command_exit_code":
        expected = int(criterion.get("exit_code", 0))
        tool_name = criterion.get("tool") or criterion.get("tool_name")
        command_match = criterion.get("command")
        query = db.query(ToolCallRecord).filter(ToolCallRecord.task_id == task.id)
        if tool_name:
            query = query.filter(ToolCallRecord.tool_name == tool_name)
        if latest_change:
            query = query.filter(ToolCallRecord.created_at >= latest_change)
        calls = query.order_by(ToolCallRecord.created_at.desc()).all()
        call = next((item for item in calls if not command_match or item.get_tool_input().get("command") == command_match), None)
        actual = call.get_result().get("exit_code") if call else None
        passed = call is not None and actual == expected
        evidence = f"Expected exit_code={expected}; actual={actual}"
        command = command_match or (call.get_tool_input().get("command") if call else tool_name or "command")
        return passed, evidence, command, actual

    if kind == "user_approval":
        approval = db.query(ExecutionLog).filter(
            ExecutionLog.goal_id == task.goal_id,
            ExecutionLog.task_id == task.id,
            ExecutionLog.event_type == "task.approved",
            ExecutionLog.event_status == "completed",
        ).order_by(ExecutionLog.created_at.desc()).first()
        return approval is not None, (
            "Human approval event recorded" if approval else "No human approval event recorded"
        ), "task.approved", 0 if approval else 1

    if kind == "review_score":
        review = db.query(SupervisorReview).filter(
            SupervisorReview.goal_id == task.goal_id
        ).order_by(SupervisorReview.created_at.desc()).first()
        score = 1.0 if review and review.passed else 0.0
        minimum = float(criterion.get("minimum", 0.8))
        passed = score >= minimum
        return passed, f"Supervisor score proxy={score:.1f}; minimum={minimum:.2f}", "supervisor_review", 0 if passed else 1

    return False, "Unsupported verification criterion", str(criterion), 1


def _task_gate_evidence(db: Session, task: Task, active_tasks: Iterable[Task]) -> Dict[str, Any]:
    criteria = task._get_json("acceptance_criteria")
    verification_required = bool(criteria) or task.task_type in DETERMINISTIC_TASK_TYPES
    reasons: List[str] = []

    if task.status == "skipped":
        return {
            "task_id": task.id,
            "title": task.title,
            "status": task.status,
            "verification_required": False,
            "satisfied": True,
            "reasons": ["Task was explicitly skipped."],
        }
    if task.status not in SUCCESS_STATUSES:
        reasons.append(f"Task status is {task.status}.")
    if not (task.output or "").strip():
        reasons.append("Model or worker output is missing.")

    if verification_required:
        if not criteria:
            reasons.append("Deterministic Task has no Completion Contract.")
        if task.status != "completed_verified" or task.verification_status != "passed":
            reasons.append("Task is not completed_verified with a passed verification status.")
        latest = _latest_verification_results(db, task.id)
        missing = [
            criterion.get("type", "unknown")
            for criterion in criteria if latest.get(criterion.get("type", "unknown")) is None
        ]
        failed = [kind for kind, result in latest.items() if result.status != "passed"]
        if missing:
            reasons.append("Missing VerificationResult: " + ", ".join(missing))
        if failed:
            reasons.append("Failed VerificationResult: " + ", ".join(failed))
        if _writes_workspace(task) and not db.query(Artifact).filter(Artifact.task_id == task.id).first():
            reasons.append("Workspace-writing Task has no tracked Artifact.")

    if task.risk_level == "high" and not _high_risk_resolved(db, task, active_tasks):
        reasons.append("High-risk Task has no recorded approval or verified downstream Reviewer.")

    return {
        "task_id": task.id,
        "title": task.title,
        "status": task.status,
        "verification_status": task.verification_status,
        "verification_required": verification_required,
        "satisfied": not reasons,
        "reasons": reasons,
    }


def _relevant_artifacts(db: Session, task: Task) -> List[Artifact]:
    task_ids = [task.id]
    if task.task_type == "verification":
        task_ids.extend(task._get_json("dependencies"))
    return db.query(Artifact).filter(Artifact.task_id.in_(task_ids)).all()


def _latest_tool_call(
    db: Session,
    task_id: str,
    tool_name: str,
    *,
    latest_change=None,
    successful_only: bool = False,
) -> Optional[ToolCallRecord]:
    query = db.query(ToolCallRecord).filter(
        ToolCallRecord.task_id == task_id,
        ToolCallRecord.tool_name == tool_name,
    )
    if successful_only:
        query = query.filter(ToolCallRecord.status == "completed")
    if latest_change:
        query = query.filter(ToolCallRecord.created_at >= latest_change)
    return query.order_by(ToolCallRecord.created_at.desc()).first()


def _latest_verification_results(db: Session, task_id: str) -> Dict[str, VerificationResult]:
    rows = db.query(VerificationResult).filter(
        VerificationResult.task_id == task_id
    ).order_by(VerificationResult.created_at.desc()).all()
    latest: Dict[str, VerificationResult] = {}
    for row in rows:
        latest.setdefault(row.criterion_type, row)
    return latest


def _writes_workspace(task: Task) -> bool:
    return task.task_type in {"coding", "merge"} or bool(
        WRITE_TOOLS.intersection(task._get_json("required_tools"))
    )


def _high_risk_resolved(db: Session, task: Task, active_tasks: Iterable[Task]) -> bool:
    approved = db.query(ExecutionLog).filter(
        ExecutionLog.goal_id == task.goal_id,
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == "task.approved",
        ExecutionLog.event_status == "completed",
    ).first()
    if approved:
        return True

    task_by_id = {candidate.id: candidate for candidate in active_tasks}

    def reviewer_covers(candidate: Task) -> bool:
        pending = list(candidate._get_json("dependencies"))
        seen = set()
        while pending:
            dependency_id = pending.pop()
            if dependency_id == task.id:
                return True
            if dependency_id in seen:
                continue
            seen.add(dependency_id)
            dependency = task_by_id.get(dependency_id)
            if dependency:
                pending.extend(dependency._get_json("dependencies"))
        return False

    return any(
        candidate.task_type == "verification"
        and candidate.status == "completed_verified"
        and candidate.verification_status == "passed"
        and reviewer_covers(candidate)
        for candidate in task_by_id.values()
    )
