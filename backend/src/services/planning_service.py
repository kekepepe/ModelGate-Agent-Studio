"""Persistence and read APIs for immutable, versioned execution plans."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Union

from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.workspace import ExecutionPlan, Goal, PlanChange, PlanTask
from src.schemas.planning import ExecutionPlanContract, PlanChangeContract, PlanTaskContract
from src.services import log_service


class PlanNotFoundError(Exception):
    pass


class PlanValidationError(Exception):
    pass


def validate_plan(payload: Union[ExecutionPlanContract, dict]) -> ExecutionPlanContract:
    if isinstance(payload, ExecutionPlanContract):
        return payload
    try:
        return ExecutionPlanContract.model_validate(payload)
    except ValidationError as exc:
        raise PlanValidationError(str(exc)) from exc


def persist_plan(
    db: Session,
    goal: Goal,
    payload: Union[ExecutionPlanContract, dict],
    *,
    planner_type: str,
    raw_output: Optional[str] = None,
    repair_records: Optional[List[dict]] = None,
    change: Optional[PlanChangeContract] = None,
    commit: bool = True,
) -> ExecutionPlan:
    """Validate and store a new immutable version without overwriting history."""
    contract = validate_plan(payload)
    previous = (
        db.query(ExecutionPlan)
        .filter(ExecutionPlan.goal_id == goal.id)
        .order_by(ExecutionPlan.version.desc())
        .first()
    )
    next_version = int(
        db.query(func.max(ExecutionPlan.version))
        .filter(ExecutionPlan.goal_id == goal.id)
        .scalar()
        or 0
    ) + 1
    stable_plan_id = previous.plan_id if previous else contract.plan_id or str(uuid.uuid4())
    plan = ExecutionPlan(
        id=str(uuid.uuid4()),
        plan_id=stable_plan_id,
        goal_id=goal.id,
        version=next_version,
        status="validated",
        task_mode=contract.task_mode,
        goal_summary=contract.goal_summary,
        activation_reason=contract.activation_reason,
        fallback_reason=contract.fallback_reason,
        planner_type=planner_type,
        raw_output=raw_output,
    )
    plan.set_json("assumptions", contract.assumptions)
    plan.set_json("required_context", contract.required_context)
    plan.set_json("final_acceptance_criteria", contract.final_acceptance_criteria)
    plan.set_json("human_approval_points", contract.human_approval_points)
    from src.services import plan_policy_service
    estimated_cost = dict(contract.estimated_cost)
    estimated_cost["multi_agent_analysis"] = plan_policy_service.analyze(contract)
    plan.set_json("estimated_cost", estimated_cost)
    plan.set_json("repair_records", repair_records or [])
    db.add(plan)
    db.flush()

    for task_contract in contract.tasks:
        plan_task = PlanTask(
            id=str(uuid.uuid4()),
            plan_version_id=plan.id,
            client_task_id=task_contract.client_task_id,
            objective=task_contract.objective,
            task_type=task_contract.task_type,
            risk_level=task_contract.risk_level,
            parallel_safe=task_contract.parallel_safe,
            context_query=task_contract.context_query,
            approval_required=task_contract.approval_required,
            workspace_scope=task_contract.workspace_scope,
            merge_strategy=task_contract.merge_strategy,
        )
        plan_task.set_json("required_capabilities", task_contract.required_capabilities)
        plan_task.set_json("required_tools", task_contract.required_tools)
        plan_task.set_json("dependencies", task_contract.dependencies)
        plan_task.set_json("acceptance_criteria", task_contract.acceptance_criteria)
        db.add(plan_task)

    if previous:
        previous.status = "superseded"
    change_contract = change or PlanChangeContract(
        change_type="created" if previous is None else "replan",
        reason=contract.activation_reason,
        added_task_ids=[task.client_task_id for task in contract.tasks],
    )
    plan_change = PlanChange(
        id=str(uuid.uuid4()),
        goal_id=goal.id,
        from_plan_version_id=previous.id if previous else None,
        to_plan_version_id=plan.id,
        change_type=change_contract.change_type,
        reason=change_contract.reason,
    )
    for field in (
        "evidence",
        "retained_task_ids",
        "cancelled_task_ids",
        "added_task_ids",
        "replaced_task_ids",
    ):
        plan_change.set_json(field, getattr(change_contract, field))
    db.add(plan_change)
    if commit:
        db.commit()
        db.refresh(plan)
        emit_plan_events(db, plan, len(contract.tasks))
    else:
        db.flush()
    return plan


def emit_plan_events(db: Session, plan: ExecutionPlan, task_count: int) -> None:
    log_service.create_log(db, {
        "goal_id": plan.goal_id,
        "event_type": "plan.created",
        "event_status": "completed",
        "output_summary": f"ExecutionPlan v{plan.version} validated with {task_count} tasks",
        "metadata": {
            "plan_id": plan.plan_id,
            "plan_version_id": plan.id,
            "version": plan.version,
            "task_mode": plan.task_mode,
            "planner_type": plan.planner_type,
        },
    })
    if plan.planner_type == "rule_fallback":
        log_service.create_log(db, {
            "goal_id": plan.goal_id,
            "event_type": "plan.fallback_used",
            "event_status": "completed",
            "output_summary": plan.fallback_reason or "Rule-based planning fallback used",
            "metadata": {"plan_version_id": plan.id, "version": plan.version},
        })


def activate_plan(
    db: Session,
    plan: ExecutionPlan,
    *,
    commit: bool = True,
    confirmed: bool = True,
) -> ExecutionPlan:
    db.query(ExecutionPlan).filter(
        ExecutionPlan.goal_id == plan.goal_id,
        ExecutionPlan.id != plan.id,
        ExecutionPlan.status == "active",
    ).update({"status": "superseded"}, synchronize_session=False)
    plan.status = "active"
    plan.confirmed_at = datetime.now(timezone.utc) if confirmed else None
    if commit:
        db.commit()
        db.refresh(plan)
    else:
        db.flush()
    return plan


def confirm_plan(db: Session, goal_id: str, version: int) -> dict:
    plan = db.query(ExecutionPlan).filter(
        ExecutionPlan.goal_id == goal_id,
        ExecutionPlan.version == version,
    ).first()
    if not plan:
        raise PlanNotFoundError(f"ExecutionPlan v{version} for Goal '{goal_id}' not found")
    if plan.status != "active":
        raise PlanValidationError("Only the active ExecutionPlan can be confirmed")
    if not plan.confirmed_at:
        plan.confirmed_at = datetime.now(timezone.utc)
        log_service.create_log(db, {
            "goal_id": goal_id,
            "event_type": "plan.confirmed",
            "event_status": "approved",
            "output_summary": f"ExecutionPlan v{version} confirmed for execution",
            "metadata": {"plan_version_id": plan.id, "version": version},
        })
        db.commit()
        db.refresh(plan)
    return serialize_plan(db, plan)


def list_plans(db: Session, goal_id: str) -> List[dict]:
    plans = (
        db.query(ExecutionPlan)
        .filter(ExecutionPlan.goal_id == goal_id)
        .order_by(ExecutionPlan.version.desc())
        .all()
    )
    return [serialize_plan(db, plan) for plan in plans]


def get_active_plan_record(db: Session, goal_id: str) -> Optional[ExecutionPlan]:
    return (
        db.query(ExecutionPlan)
        .filter(ExecutionPlan.goal_id == goal_id, ExecutionPlan.status == "active")
        .order_by(ExecutionPlan.version.desc())
        .first()
    )


def contract_from_plan(db: Session, plan: ExecutionPlan) -> ExecutionPlanContract:
    tasks = (
        db.query(PlanTask)
        .filter(PlanTask.plan_version_id == plan.id)
        .order_by(PlanTask.created_at.asc(), PlanTask.client_task_id.asc())
        .all()
    )
    return ExecutionPlanContract(
        plan_id=plan.plan_id,
        version=plan.version,
        task_mode=plan.task_mode,
        goal_summary=plan.goal_summary,
        assumptions=plan._get_json("assumptions", []),
        required_context=plan._get_json("required_context", []),
        activation_reason=plan.activation_reason,
        tasks=[
            PlanTaskContract(
                client_task_id=task.client_task_id,
                objective=task.objective,
                task_type=task.task_type,
                required_capabilities=task._get_json("required_capabilities"),
                required_tools=task._get_json("required_tools"),
                dependencies=task._get_json("dependencies"),
                acceptance_criteria=task._get_json("acceptance_criteria"),
                risk_level=task.risk_level,
                parallel_safe=task.parallel_safe,
                context_query=task.context_query,
                approval_required=task.approval_required,
                workspace_scope=task.workspace_scope,
                merge_strategy=task.merge_strategy,
            )
            for task in tasks
        ],
        final_acceptance_criteria=plan._get_json("final_acceptance_criteria", []),
        human_approval_points=plan._get_json("human_approval_points", []),
        estimated_cost=plan._get_json("estimated_cost", {}),
        fallback_reason=plan.fallback_reason,
    )


def get_plan(db: Session, goal_id: str, version: int) -> dict:
    plan = db.query(ExecutionPlan).filter(
        ExecutionPlan.goal_id == goal_id,
        ExecutionPlan.version == version,
    ).first()
    if not plan:
        raise PlanNotFoundError(f"ExecutionPlan v{version} for Goal '{goal_id}' not found")
    return serialize_plan(db, plan)


def serialize_plan(db: Session, plan: ExecutionPlan) -> dict:
    tasks = (
        db.query(PlanTask)
        .filter(PlanTask.plan_version_id == plan.id)
        .order_by(PlanTask.created_at.asc())
        .all()
    )
    return plan.to_dict(tasks)
