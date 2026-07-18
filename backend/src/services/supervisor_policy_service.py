"""Policy gate for activating an independent Goal-level Supervisor."""

from typing import Dict, List

from sqlalchemy.orm import Session

from src.models.handoff import ExecutionLog, HandoffRecord
from src.models.workspace import ExecutionPlan, Goal, Task


DETERMINISTIC_CRITERIA = {
    "diff_exists", "tests_pass", "lint_pass", "typecheck_pass", "build_pass",
    "file_exists", "command_exit_code", "user_approval",
}


def evaluate(db: Session, goal: Goal, tasks: List[Task]) -> Dict:
    reasons = []
    active_plan = db.query(ExecutionPlan).filter(
        ExecutionPlan.goal_id == goal.id, ExecutionPlan.status == "active",
    ).order_by(ExecutionPlan.version.desc()).first()
    if any(task.risk_level == "high" for task in tasks):
        reasons.append("The active plan contains a high-risk Task.")
    if active_plan and active_plan.task_mode == "parallel_multi_agent":
        reasons.append("Parallel branches require an independent Goal-level merge judgment.")
    if any(task.status in {"failed", "revision_required", "blocked"} or task.retry_count > 0 for task in tasks):
        reasons.append("The run contains a failure, revision, block or retry.")
    if db.query(HandoffRecord.id).filter(HandoffRecord.goal_id == goal.id).first():
        reasons.append("The run contains a Handoff.")
    if db.query(ExecutionLog.id).filter(
        ExecutionLog.goal_id == goal.id,
        ExecutionLog.event_type.in_(["plan.replanned", "replan.created", "task.replanned"]),
    ).first():
        reasons.append("The run contains a Replan.")
    description = f"{goal.title} {goal.description or ''}".lower()
    if any(phrase in description for phrase in ("independent review", "独立审查", "supervisor review", "人工复核")):
        reasons.append("The user requested an independent review.")
    subjective = sorted({
        criterion.get("type", "")
        for task in tasks for criterion in task._get_json("acceptance_criteria")
        if criterion.get("type") not in DETERMINISTIC_CRITERIA
    })
    if subjective:
        reasons.append(f"Subjective completion criteria require review: {', '.join(subjective)}.")
    if not reasons:
        return {
            "activate": False,
            "reasons": ["All required work is low-risk and covered by deterministic verification."],
            "policy": "on_demand_supervisor_v1",
        }
    return {"activate": True, "reasons": reasons, "policy": "on_demand_supervisor_v1"}
