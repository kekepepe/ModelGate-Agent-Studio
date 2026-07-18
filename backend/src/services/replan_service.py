"""Versioned Replan protocol for graph edits and evidence-backed repair work."""

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Set

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.workspace import ExecutionPlan, Goal, PlanChange, PlanTask, Task
from src.schemas.planning import (
    ExecutionPlanContract,
    PlanChangeContract,
    PlanTaskContract,
    ReplanRequest,
    RuntimeDecisionContract,
)
from src.services import goal_service, log_service, planning_service


class ReplanError(RuntimeError):
    pass


class ReplanConflictError(ReplanError):
    pass


FAILURE_STATUSES = {"failed", "blocked", "revision_required"}
TERMINAL_STATUSES = {
    "completed",
    "completed_verified",
    "completed_unverified",
    "failed",
    "blocked",
    "revision_required",
    "cancelled",
    "skipped",
}
MAX_AUTOMATIC_REPLANS = 3


def request_replan(db: Session, goal_id: str, request: ReplanRequest) -> Dict:
    goal = goal_service.get_goal(db, goal_id)
    running = db.query(Task).filter(Task.goal_id == goal.id, Task.status == "running").first()
    if running:
        raise ReplanConflictError(
            f"Task '{running.id}' is running; pause the run before replacing its plan"
        )

    active_plan = ensure_active_plan(db, goal)
    old_plan_tasks = _plan_tasks(db, active_plan)
    old_runtime_by_client = _runtime_by_client(db, old_plan_tasks)
    old_contract = planning_service.contract_from_plan(db, active_plan)

    replacement_runtime_ids = set(request.replace_task_ids)
    unknown = replacement_runtime_ids - {task.id for task in old_runtime_by_client.values()}
    if unknown:
        raise ReplanError("Replacement Tasks are not part of the active Plan: " + ", ".join(sorted(unknown)))
    if not replacement_runtime_ids and request.plan is None:
        replacement_runtime_ids = {
            task.id
            for task in old_runtime_by_client.values()
            if task.status in FAILURE_STATUSES
            or (task.task_type in {"coding", "verification"} and task.status != "completed_verified")
        }
    if request.plan is None and not replacement_runtime_ids:
        raise ReplanError("No failed or unverified Task is available to replace")
    from src.services import context_service
    replan_context = context_service.build_replan_context(
        db,
        goal,
        [task for task in old_runtime_by_client.values() if task.id in replacement_runtime_ids],
        request.reason,
    )

    contract = request.plan or _replacement_contract(
        old_contract,
        old_runtime_by_client,
        replacement_runtime_ids,
        request.reason,
    )
    contract = contract.model_copy(update={
        "plan_id": active_plan.plan_id,
        "version": active_plan.version + 1,
        "activation_reason": request.reason,
    })

    old_plan_task_by_client = {task.client_task_id: task for task in old_plan_tasks}
    retained: Dict[str, Task] = {}
    agents: Dict[str, AgentStation] = {}
    replaced_clients: Set[str] = set()
    added_clients: Set[str] = set()
    source_by_client: Dict[str, str] = {}
    parent_by_client: Dict[str, str] = {}

    from src.services.model_orchestrator_service import ModelOrchestrator, ModelPlanningFailed
    resolver = ModelOrchestrator()
    for new_task in contract.tasks:
        old_plan_task = old_plan_task_by_client.get(new_task.client_task_id)
        old_runtime = old_runtime_by_client.get(new_task.client_task_id)
        unchanged = bool(old_plan_task and _task_semantics_match(old_plan_task, new_task))
        explicitly_replaced = bool(old_runtime and old_runtime.id in replacement_runtime_ids)
        failed = bool(old_runtime and old_runtime.status in FAILURE_STATUSES)
        can_retain = bool(
            old_runtime
            and unchanged
            and not explicitly_replaced
            and not failed
            and (request.preserve_verified or old_runtime.status != "completed_verified")
        )
        if can_retain:
            retained[new_task.client_task_id] = old_runtime
            source_by_client[new_task.client_task_id] = "retained"
            continue
        if old_runtime:
            replaced_clients.add(new_task.client_task_id)
            parent_by_client[new_task.client_task_id] = old_runtime.id
            source_by_client[new_task.client_task_id] = "replaced"
            agents[new_task.client_task_id] = _existing_or_resolved_agent(db, old_runtime, new_task, resolver)
        else:
            added_clients.add(new_task.client_task_id)
            source_by_client[new_task.client_task_id] = "added"
            try:
                agents[new_task.client_task_id] = resolver.resolve_task_agent(db, new_task)
            except ModelPlanningFailed as exc:
                raise ReplanError(str(exc)) from exc

    new_client_ids = {task.client_task_id for task in contract.tasks}
    cancelled_clients = set(old_plan_task_by_client) - new_client_ids
    change = PlanChangeContract(
        change_type="replan",
        reason=request.reason,
        evidence=[{"trigger": request.trigger}, *request.evidence, {"replan_context": replan_context}],
        retained_task_ids=sorted(retained),
        cancelled_task_ids=sorted(cancelled_clients),
        added_task_ids=sorted(added_clients),
        replaced_task_ids=sorted(replaced_clients),
    )

    goal.status = "replanning"
    goal.updated_at = datetime.now(timezone.utc)
    try:
        plan = planning_service.persist_plan(
            db,
            goal,
            contract,
            planner_type="runtime_replan",
            raw_output=contract.model_dump_json(),
            change=change,
            commit=False,
        )
        _cancel_obsolete_runtime_tasks(
            old_runtime_by_client,
            cancelled_clients | replaced_clients,
            request.reason,
        )
        from src.services.orchestrator_service import _materialize_plan
        created = _materialize_plan(
            db,
            goal,
            plan,
            agents,
            retained_runtime_by_client_id=retained,
            replacement_parent_by_client_id=parent_by_client,
            source_by_client_id=source_by_client,
            commit=False,
        )
        planning_service.activate_plan(db, plan, commit=False)
        goal.status = "running" if created or _has_unfinished(retained.values()) else "completed"
        db.commit()
        db.refresh(plan)
    except Exception as exc:
        db.rollback()
        if isinstance(exc, ReplanError):
            raise
        raise ReplanError(str(exc)) from exc

    planning_service.emit_plan_events(db, plan, len(contract.tasks))
    log_service.create_log(db, {
        "goal_id": goal.id,
        "event_type": "plan.replan_requested",
        "event_status": "completed",
        "output_summary": request.reason,
        "metadata": {
            "trigger": request.trigger,
            "from_plan_version": active_plan.version,
            "to_plan_version": plan.version,
            "evidence": request.evidence,
        },
    })
    log_service.create_log(db, {
        "goal_id": goal.id,
        "event_type": "plan.updated",
        "event_status": "completed",
        "output_summary": (
            f"Plan v{active_plan.version} -> v{plan.version}: "
            f"retained={len(retained)}, replaced={len(replaced_clients)}, "
            f"added={len(added_clients)}, cancelled={len(cancelled_clients)}"
        ),
        "metadata": change.model_dump(),
    })
    decision = RuntimeDecisionContract(
        action="replan_graph",
        reason=request.reason,
        evidence=request.evidence,
    )
    return {
        "decision": decision.model_dump(),
        "plan": planning_service.serialize_plan(db, plan),
        "change": change.model_dump(),
        "created_task_ids": [task.id for task in created],
        "goal_status": goal.status,
    }


def replan_failed_tasks(
    db: Session,
    goal: Goal,
    failed_tasks: Iterable[Task],
    *,
    reason: str,
    evidence: Optional[List[dict]] = None,
) -> Dict:
    task_ids = [task.id for task in failed_tasks]
    return request_replan(db, goal.id, ReplanRequest(
        trigger="supervisor_review",
        reason=reason,
        evidence=evidence or [],
        replace_task_ids=task_ids,
    ))


def request_automatic_replan(
    db: Session,
    goal_id: str,
    *,
    trigger: str,
    reason: str,
    task_ids: List[str],
    evidence: Optional[List[dict]] = None,
) -> Optional[Dict]:
    replan_count = db.query(PlanChange).filter(
        PlanChange.goal_id == goal_id,
        PlanChange.change_type == "replan",
    ).count()
    if replan_count >= MAX_AUTOMATIC_REPLANS:
        log_service.create_log(db, {
            "goal_id": goal_id,
            "event_type": "plan.replan_requested",
            "event_status": "blocked",
            "output_summary": (
                f"Automatic Replan limit reached ({replan_count}/{MAX_AUTOMATIC_REPLANS}): {reason}"
            ),
            "metadata": {"trigger": trigger, "task_ids": task_ids, "evidence": evidence or []},
        })
        return None
    return request_replan(db, goal_id, ReplanRequest(
        trigger=trigger,
        reason=reason,
        evidence=evidence or [],
        replace_task_ids=task_ids,
    ))


def get_active_runtime_tasks(db: Session, goal_id: str) -> List[Task]:
    active = planning_service.get_active_plan_record(db, goal_id)
    if not active:
        return db.query(Task).filter(Task.goal_id == goal_id).all()
    runtime_ids = [
        task.runtime_task_id
        for task in _plan_tasks(db, active)
        if task.runtime_task_id
    ]
    if not runtime_ids:
        return []
    tasks = db.query(Task).filter(Task.id.in_(runtime_ids)).all()
    by_id = {task.id: task for task in tasks}
    return [by_id[task_id] for task_id in runtime_ids if task_id in by_id]


def ensure_active_plan(db: Session, goal: Goal) -> ExecutionPlan:
    active = planning_service.get_active_plan_record(db, goal.id)
    if active:
        return active
    tasks = db.query(Task).filter(Task.goal_id == goal.id).order_by(Task.created_at.asc()).all()
    if not tasks:
        raise ReplanError("Goal has no Task graph to replan")
    agents = {
        client_id: db.query(AgentStation).filter(AgentStation.id == task.assigned_agent_id).first()
        for client_id, task in zip(
            [f"legacy-{index + 1}" for index in range(len(tasks))],
            tasks,
        )
        if task.assigned_agent_id
    }
    contract = _legacy_contract(goal, tasks, agents)
    retained = {item.client_task_id: task for item, task in zip(contract.tasks, tasks)}
    plan = planning_service.persist_plan(
        db,
        goal,
        contract,
        planner_type="legacy_import",
        raw_output=contract.model_dump_json(),
        commit=False,
    )
    from src.services.orchestrator_service import _materialize_plan
    _materialize_plan(
        db,
        goal,
        plan,
        agents,
        retained_runtime_by_client_id=retained,
        source_by_client_id={key: "retained" for key in retained},
        commit=False,
    )
    planning_service.activate_plan(db, plan, commit=False)
    db.commit()
    db.refresh(plan)
    planning_service.emit_plan_events(db, plan, len(contract.tasks))
    return plan


def _plan_tasks(db: Session, plan: ExecutionPlan) -> List[PlanTask]:
    return (
        db.query(PlanTask)
        .filter(PlanTask.plan_version_id == plan.id)
        .order_by(PlanTask.created_at.asc(), PlanTask.client_task_id.asc())
        .all()
    )


def _runtime_by_client(db: Session, plan_tasks: Iterable[PlanTask]) -> Dict[str, Task]:
    result = {}
    for plan_task in plan_tasks:
        if not plan_task.runtime_task_id:
            continue
        runtime = db.query(Task).filter(Task.id == plan_task.runtime_task_id).first()
        if runtime:
            result[plan_task.client_task_id] = runtime
    return result


def _replacement_contract(
    old: ExecutionPlanContract,
    runtime_by_client: Dict[str, Task],
    replacement_runtime_ids: Set[str],
    reason: str,
) -> ExecutionPlanContract:
    tasks = []
    for task in old.tasks:
        runtime = runtime_by_client.get(task.client_task_id)
        if runtime and runtime.id in replacement_runtime_ids:
            tasks.append(task.model_copy(update={
                "objective": f"Revise: {task.objective}",
                "context_query": f"{task.context_query}\nReplan reason: {reason}".strip(),
            }))
        else:
            tasks.append(task)
    return old.model_copy(update={"tasks": tasks, "activation_reason": reason})


def _task_semantics_match(old: PlanTask, new: PlanTaskContract) -> bool:
    return (
        old.objective == new.objective
        and old.task_type == new.task_type
        and old._get_json("required_capabilities") == new.required_capabilities
        and old._get_json("required_tools") == new.required_tools
        and old._get_json("acceptance_criteria") == new.acceptance_criteria
        and old.risk_level == new.risk_level
        and old.parallel_safe == new.parallel_safe
        and old.context_query == new.context_query
        and old.approval_required == new.approval_required
        and old.workspace_scope == new.workspace_scope
        and old.merge_strategy == new.merge_strategy
    )


def _existing_or_resolved_agent(db: Session, runtime: Task, task: PlanTaskContract, resolver) -> AgentStation:
    existing = db.query(AgentStation).filter(
        AgentStation.id == runtime.assigned_agent_id,
        AgentStation.is_enabled == True,
    ).first()
    if existing:
        return existing
    try:
        return resolver.resolve_task_agent(db, task)
    except Exception as exc:
        raise ReplanError(str(exc)) from exc


def _cancel_obsolete_runtime_tasks(
    runtime_by_client: Dict[str, Task],
    client_ids: Set[str],
    reason: str,
) -> None:
    for client_id in client_ids:
        runtime = runtime_by_client.get(client_id)
        if runtime and runtime.status not in TERMINAL_STATUSES:
            runtime.status = "cancelled"
            runtime.blocked_reason = f"Superseded by Replan: {reason}"


def _has_unfinished(tasks: Iterable[Task]) -> bool:
    return any(task.status not in TERMINAL_STATUSES for task in tasks)


def _legacy_contract(
    goal: Goal,
    tasks: List[Task],
    agents: Optional[Dict[str, AgentStation]] = None,
) -> ExecutionPlanContract:
    client_ids = [f"legacy-{index + 1}" for index in range(len(tasks))]
    id_to_client = {task.id: client_id for task, client_id in zip(tasks, client_ids)}
    contracts = []
    agents = agents or {}
    role_task_types = {
        "planner": "planning",
        "research": "research",
        "coder": "coding",
        "reviewer": "verification",
        "summarizer": "direct",
        "supervisor": "verification",
    }
    for task, client_id in zip(tasks, client_ids):
        task_type = task.task_type if task.task_type in {
            "direct", "planning", "research", "coding", "verification", "merge"
        } else "direct"
        assigned_agent = agents.get(client_id)
        if task.task_type not in {
            "direct", "planning", "research", "coding", "verification", "merge"
        } and assigned_agent:
            task_type = role_task_types.get(assigned_agent.role, task_type)
        criteria = task._get_json("acceptance_criteria")
        if task_type in {"coding", "merge"} and not criteria:
            criteria = [{"type": "diff_exists"}]
        capabilities = task._get_json("required_capabilities") or {
            "direct": ["direct"], "planning": ["planning"], "research": ["research"],
            "coding": ["code_edit"], "verification": ["review"], "merge": ["code_edit"],
        }[task_type]
        parallel_safe = "parallel_safe" in capabilities
        merge_strategy = (
            "legacy_isolated_worktree_patch"
            if parallel_safe and task_type in {"coding", "merge"}
            else None
        )
        contracts.append(PlanTaskContract(
            client_task_id=client_id,
            objective=task.title,
            task_type=task_type,
            required_capabilities=[item for item in capabilities if item != "parallel_safe"],
            required_tools=task._get_json("required_tools"),
            dependencies=[id_to_client[item] for item in task._get_json("dependencies") if item in id_to_client],
            acceptance_criteria=criteria,
            risk_level=task.risk_level,
            parallel_safe=parallel_safe,
            approval_required=task.risk_level == "high",
            context_query=task.description or task.title,
            merge_strategy=merge_strategy,
        ))
    parallel_count = sum(task.parallel_safe for task in contracts)
    if len(contracts) == 1 and contracts[0].task_type == "direct":
        mode = "direct"
    elif len(contracts) == 1:
        mode = "single_agent"
    elif parallel_count >= 2:
        mode = "parallel_multi_agent"
    else:
        mode = "sequential_multi_agent"
    return ExecutionPlanContract(
        task_mode=mode,
        goal_summary=goal.description or goal.title,
        activation_reason="Imported the legacy Task graph before versioned Replan.",
        tasks=contracts,
    )
