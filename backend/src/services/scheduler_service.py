"""Validated DAG scheduling decisions for one Goal run."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.handoff import ExecutionLog
from src.models.agent import AgentStation
from src.models.workspace import Goal, Task
from src.services import log_service


SUCCESS_STATUSES = {"completed", "completed_verified", "completed_unverified", "skipped"}
FAILURE_STATUSES = {"failed", "blocked", "cancelled", "revision_required"}
SCHEDULABLE_STATUSES = {"pending", "ready", "assigned"}


@dataclass
class SchedulingDecision:
    ready_tasks: List[Task] = field(default_factory=list)
    selected_tasks: List[Task] = field(default_factory=list)
    blocked_reason: Optional[str] = None
    goal_status: Optional[str] = None
    invalid_task_ids: List[str] = field(default_factory=list)


def schedule_ready_tasks(db: Session, goal: Goal) -> SchedulingDecision:
    tasks = db.query(Task).filter(Task.goal_id == goal.id).all()
    if not tasks:
        return SchedulingDecision(
            blocked_reason="Goal has no executable tasks",
            goal_status="blocked",
        )

    task_by_id = {task.id: task for task in tasks}
    invalid_reasons = _validate_runtime_graph(tasks, task_by_id)
    if invalid_reasons:
        invalid_ids = sorted(invalid_reasons)
        for task_id, reason in invalid_reasons.items():
            task = task_by_id[task_id]
            task.status = "blocked"
            task.blocked_reason = reason
            _log_once(db, task, "task.blocked", "blocked", reason)
        db.commit()
        return SchedulingDecision(
            blocked_reason="Invalid Task DAG: " + "; ".join(sorted(set(invalid_reasons.values()))),
            goal_status="blocked",
            invalid_task_ids=invalid_ids,
        )

    ready: List[Task] = []
    for task in tasks:
        if task.status not in SCHEDULABLE_STATUSES:
            continue
        dependencies = [task_by_id[dependency] for dependency in task._get_json("dependencies")]
        failed_dependencies = [dependency for dependency in dependencies if dependency.status in FAILURE_STATUSES]
        if failed_dependencies:
            task.status = "blocked"
            task.blocked_reason = "Dependency did not complete successfully: " + ", ".join(
                dependency.id for dependency in failed_dependencies
            )
            _log_once(db, task, "task.blocked", "blocked", task.blocked_reason)
            continue
        if all(dependency.status in SUCCESS_STATUSES for dependency in dependencies):
            if task.status == "pending":
                task.status = "ready"
            ready.append(task)
            _log_once(
                db,
                task,
                "task.ready",
                "completed",
                f"Task is ready after {len(dependencies)} dependencies",
            )
    db.commit()

    ready.sort(key=lambda task: (-task.priority, task.created_at))
    if ready:
        parallel = [
            task for task in ready
            if "parallel_safe" in task._get_json("required_capabilities")
        ]
        if len(parallel) >= 2:
            selected = _select_with_agent_capacity(
                db, parallel, max(1, goal.max_parallel_tasks or 1),
            )
            if len(selected) >= 2:
                log_service.create_log(db, {
                    "goal_id": goal.id,
                    "event_type": "task.parallel_group_started",
                    "event_status": "started",
                    "output_summary": f"Scheduled {len(selected)} isolated parallel tasks",
                    "metadata": {
                        "task_ids": [task.id for task in selected],
                        "max_parallel_tasks": goal.max_parallel_tasks,
                    },
                })
                return SchedulingDecision(ready_tasks=ready, selected_tasks=selected)
        return SchedulingDecision(ready_tasks=ready, selected_tasks=[ready[0]])

    waiting = [task for task in tasks if task.status == "waiting_approval"]
    if waiting:
        return SchedulingDecision(
            blocked_reason="Human approval is required before execution can continue",
            goal_status="waiting_approval",
        )
    replanning = [task for task in tasks if task.status == "replanning"]
    if replanning:
        return SchedulingDecision(
            blocked_reason="A plan update is required before execution can continue",
            goal_status="replanning",
        )
    unfinished = [task for task in tasks if task.status not in SUCCESS_STATUSES]
    if unfinished:
        details = ", ".join(f"{task.id}:{task.status}" for task in unfinished[:5])
        return SchedulingDecision(
            blocked_reason=f"No ready Task exists while unfinished Tasks remain ({details})",
            goal_status="blocked",
        )
    return SchedulingDecision()


def _select_with_agent_capacity(db: Session, tasks: List[Task], limit: int) -> List[Task]:
    """Do not claim parallelism when one Agent has no concurrent capacity."""
    agent_ids = {task.assigned_agent_id for task in tasks if task.assigned_agent_id}
    agents = {
        agent.id: agent for agent in db.query(AgentStation).filter(AgentStation.id.in_(agent_ids)).all()
    } if agent_ids else {}
    active_counts: Dict[str, int] = {}
    for assigned_agent_id, count in db.query(Task.assigned_agent_id, func.count(Task.id)).filter(
        Task.assigned_agent_id.in_(agent_ids), Task.status.in_(["assigned", "running"]),
    ).group_by(Task.assigned_agent_id).all() if agent_ids else []:
        active_counts[assigned_agent_id] = count
    reserved: Dict[str, int] = {}
    selected = []
    for task in tasks:
        if len(selected) >= limit:
            break
        if not task.assigned_agent_id:
            selected.append(task)
            continue
        agent = agents.get(task.assigned_agent_id)
        capacity = max(1, agent.max_concurrency if agent else 1)
        used = active_counts.get(task.assigned_agent_id, 0) + reserved.get(task.assigned_agent_id, 0)
        if used >= capacity:
            continue
        selected.append(task)
        reserved[task.assigned_agent_id] = reserved.get(task.assigned_agent_id, 0) + 1
    return selected


def _validate_runtime_graph(tasks: List[Task], task_by_id: Dict[str, Task]) -> Dict[str, str]:
    invalid: Dict[str, str] = {}
    graph: Dict[str, List[str]] = {}
    for task in tasks:
        dependencies = task._get_json("dependencies")
        graph[task.id] = dependencies
        missing = sorted(set(dependencies) - set(task_by_id))
        if missing:
            invalid[task.id] = "Missing dependencies: " + ", ".join(missing)
        if task.id in dependencies:
            invalid[task.id] = "Task cannot depend on itself"

    visiting: Set[str] = set()
    visited: Set[str] = set()

    def visit(task_id: str, path: List[str]) -> None:
        if task_id in visiting:
            cycle_start = path.index(task_id) if task_id in path else 0
            cycle = path[cycle_start:] + [task_id]
            reason = "Dependency cycle: " + " -> ".join(cycle)
            for cycle_task_id in cycle:
                invalid[cycle_task_id] = reason
            return
        if task_id in visited or task_id not in graph:
            return
        visiting.add(task_id)
        for dependency in graph[task_id]:
            visit(dependency, path + [task_id])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in graph:
        visit(task_id, [])
    return invalid


def _log_once(db: Session, task: Task, event_type: str, event_status: str, summary: str) -> None:
    exists = db.query(ExecutionLog).filter(
        ExecutionLog.goal_id == task.goal_id,
        ExecutionLog.task_id == task.id,
        ExecutionLog.event_type == event_type,
        ExecutionLog.event_status == event_status,
    ).first()
    if exists:
        return
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "event_type": event_type,
        "event_status": event_status,
        "output_summary": summary,
    })
