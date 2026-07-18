"""Supervisor review service.

After all tasks complete, generates a review assessing:
  1. Whether all tasks completed
  2. Output quality and completeness
  3. Whether the goal is fully met
  4. Any issues or gaps found
  5. Whether revision or supplementary tasks are needed
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.supervisor import SupervisorReview
from src.models.workspace import Goal, Task
from src.models.model import Model
from src.services import log_service
from src.services.providers import get_provider
from src.services.providers.base import ModelRequest


class ReviewError(Exception):
    pass


def generate_review(db: Session, goal_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate a supervisor review for a completed goal.

    Analyzes all task outputs, aggregates them, and assesses overall quality.
    Uses the reviewer/supervisor agent and Mock Provider to generate the review.

    Returns the review dict.
    """
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise ReviewError(f"Goal '{goal_id}' not found")

    from src.services import replan_service
    tasks = replan_service.get_active_runtime_tasks(db, goal_id)
    completed = [t for t in tasks if t.status in ("completed", "completed_verified", "completed_unverified")]
    failed = [t for t in tasks if t.status == "failed"]

    # Find a supervisor or reviewer agent, or fall back to planner
    supervisor = db.query(AgentStation).filter(
        AgentStation.role.in_(["supervisor", "reviewer"]),
        AgentStation.is_enabled == True,
    ).first()
    if not supervisor:
        supervisor = db.query(AgentStation).filter(
            AgentStation.role == "planner",
            AgentStation.is_enabled == True,
        ).first()

    # Build review prompt
    task_summaries = []
    for t in tasks:
        task_summaries.append(
            f"Task: {t.title} | Status: {t.status}\n"
            f"Output: {(t.output or 'N/A')[:300]}\n"
            f"Tokens: {t.tokens_used}, Duration: {t.duration_ms}ms"
        )
    all_outputs = "\n\n".join(task_summaries)

    logs = db.query(ExecutionLog).filter(ExecutionLog.goal_id == goal_id).all()
    errors = [l for l in logs if l.event_status in ("error", "failed")]
    handoffs = [l for l in logs if l.event_type in ("handoff_created", "handoff_completed")]

    review_prompt = (
        f"Goal: {goal.title}\n"
        f"Status: {goal.status}\n\n"
        f"=== Task Outputs ===\n{all_outputs}\n\n"
        f"=== Stats ===\n"
        f"Total tasks: {len(tasks)}, Completed: {len(completed)}, Failed: {len(failed)}\n"
        f"Errors logged: {len(errors)}, Handoffs: {len(handoffs)}\n\n"
        f"As the Supervisor Agent, review the above execution results and provide:\n"
        f"1. Overall assessment: Did we achieve the goal?\n"
        f"2. Issues found (list specific problems if any)\n"
        f"3. Suggested next actions (if revision needed)\n"
        f"4. Pass/Fail decision"
    )

    try:
        import asyncio
        model_id = supervisor.default_model_id if supervisor else "model-gpt-4-turbo"
        model = db.query(Model).filter(Model.id == model_id).first()
        provider = get_provider(model=model, execution_mode=goal.execution_mode)
        req = ModelRequest(
            provider=model.provider if model else "unknown",
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a Supervisor Agent reviewing task execution results."},
                {"role": "user", "content": review_prompt},
            ],
            metadata={"provider_model_name": model.model_name if model else model_id},
        )
        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(provider.generate(req))
        loop.close()
    except Exception as e:
        # Fallback: generate a basic review without model call
        response_content = f"Review generated without model call.\nCompleted: {len(completed)}/{len(tasks)} tasks.\nFailed: {len(failed)} tasks.\nErrors: {len(errors)}.\nHandoffs: {len(handoffs)}."
        response_tokens = 0
        review_agent_id = None
        review_model_id = None
        response_latency = 0
    else:
        response_content = response.content
        response_tokens = response.total_tokens
        review_agent_id = supervisor.id if supervisor else None
        review_model_id = model_id
        response_latency = response.latency_ms

    # Parse structured result from response
    verification_failures = [task for task in tasks if task.task_type in {"coding", "merge", "verification"} and task.status != "completed_verified"]
    all_completed = len(failed) == 0 and len(completed) > 0 and not verification_failures
    has_errors = len(errors) > 0 or len(failed) > 0
    review_passed = all_completed and not has_errors

    # Extract issues from response
    issues = _extract_issues(response_content, errors, failed, handoffs)
    suggested = [] if review_passed else _build_suggested_tasks(response_content, goal, tasks)
    created_replans = []
    if verification_failures:
        try:
            replan_result = replan_service.replan_failed_tasks(
                db,
                goal,
                verification_failures,
                reason="Supervisor verification found incomplete completion evidence.",
                evidence=[
                    {
                        "task_id": task.id,
                        "status": task.status,
                        "verification_status": task.verification_status,
                    }
                    for task in verification_failures
                ],
            )
            created_replans = replan_result["created_task_ids"]
        except replan_service.ReplanError as exc:
            issues.append(f"Replan failed: {exc}")

    # Write review
    review = SupervisorReview(
        id=str(uuid.uuid4()),
        goal_id=goal_id,
        run_id=run_id,
        status="completed",
        summary=response_content[:1000] if response_content else None,
        passed=review_passed,
        reviewer_agent_id=review_agent_id,
        reviewer_model_id=review_model_id,
        tokens_used=response_tokens,
    )
    review.set_issues(issues)
    review.set_suggested_tasks(suggested)
    db.add(review)

    # Log the review
    log_service.create_log(db, {
        "goal_id": goal_id,
        "event_type": "supervisor_review",
        "event_status": "approved" if review_passed else "needs_revision",
        "output_summary": (response_content or "")[:200],
        "agent_id": review_agent_id,
        "model_id": review_model_id,
        "metadata": {
            "passed": review_passed,
            "issues_count": len(issues),
            "suggested_tasks": len(suggested), "created_replans": len(created_replans),
            "completed_count": len(completed),
            "failed_count": len(failed),
            "latency_ms": response_latency,
        },
    })
    db.commit()
    db.refresh(review)

    # Update goal status based on review
    if review_passed:
        from src.services import verifier_service
        gate = verifier_service.evaluate_goal_completion(db, goal)
        goal.status = gate["goal_status"]
        goal.final_verification_status = gate["status"]
    elif created_replans:
        # The new tasks are runnable on the next Runtime invocation; keep the
        # Workspace action enabled instead of leaving a dead review state.
        goal.status = "running"
    elif suggested:
        goal.status = "revision_required"
    else:
        # A failed Supervisor decision can never promote the Goal merely
        # because it did not manage to produce a repair suggestion.
        goal.status = "revision_required"
    goal.updated_at = datetime.now(timezone.utc)
    db.commit()

    return review.to_dict()


def get_review(db: Session, goal_id: str) -> Optional[Dict[str, Any]]:
    """Get the latest supervisor review for a goal."""
    review = db.query(SupervisorReview).filter(
        SupervisorReview.goal_id == goal_id
    ).order_by(SupervisorReview.created_at.desc()).first()
    return review.to_dict() if review else None


def _extract_issues(
    response: str,
    errors: List,
    failed: List,
    handoffs: List,
) -> List[str]:
    issues = []
    if failed:
        issues.append(f"{len(failed)} task(s) failed: {', '.join(t.title for t in failed)}")
    if errors:
        error_msgs = {e.error_message or e.event_type for e in errors[:5]}
        issues.extend(list(error_msgs))
    if handoffs:
        issues.append(f"Execution required {len(handoffs)} handoff(s)")
    if not issues and "issue" in response.lower():
        for line in response.split("\n"):
            if "issue" in line.lower() or "problem" in line.lower() or "⚠" in line:
                issues.append(line.strip().lstrip("-_• 0123456789.)"))
    return issues[:10]


def _build_suggested_tasks(
    response: str,
    goal: Goal,
    tasks: List,
) -> List[Dict[str, str]]:
    incomplete = [t for t in tasks if t.status not in ("completed", "completed_verified", "completed_unverified")]
    suggested = []
    for t in incomplete:
        suggested.append({
            "title": f"Re-run: {t.title}",
            "description": f"Previous status: {t.status}. Please re-execute the task: {t.title}",
            "status": "pending",
            "agent_id": t.assigned_agent_id or "",
        })
    return suggested
