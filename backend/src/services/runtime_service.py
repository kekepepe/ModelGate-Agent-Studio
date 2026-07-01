"""Runtime orchestrator: Goal -> Task -> Worker -> Model -> Logs -> Quota -> Handoff -> Output.

Orchestrates the full execution pipeline by stitching together existing
services from all 6 modules. Uses a mock model provider (swappable to
real OpenAI-compatible provider via the ModelProvider Protocol).
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord, HandoffTask, WorkerSession
from src.models.model import Model
from src.models.workspace import Goal, Task
from src.services import (
    goal_service,
    handoff_service,
    log_service,
    quota_service,
    router_service,
    task_service,
)
from src.services.providers import get_provider
from src.services.providers.base import ModelRequest


class RuntimeError(Exception):
    pass


class GoalNotReadyError(RuntimeError):
    pass


class TaskNotReadyError(RuntimeError):
    pass


ROLE_TO_TASK_TYPE = {
    "planner": "planning",
    "coder": "coding",
    "reviewer": "review",
    "research": "research",
    "summarizer": "summarization",
    "supervisor": "supervision",
}


def execute_goal_pipeline(db: Session, goal_id: str) -> Dict[str, Any]:
    """Execute the full goal pipeline: Plan -> Execute Tasks -> Complete."""
    goal = goal_service.get_goal(db, goal_id)
    if goal.status not in ("planning", "running"):
        raise GoalNotReadyError(f"Goal must be planning or running, current: {goal.status}")

    start_time = time.time()
    total_tokens = 0
    tasks_completed = 0
    tasks_failed = 0
    tasks_handoff = 0
    execution_log: List[Dict[str, Any]] = []

    if goal.status == "planning":
        goal.status = "running"
        goal.updated_at = datetime.now(timezone.utc)
        db.commit()

    # Phase 1: Find and execute planner task
    planner_task = _find_planner_task(db, goal_id)
    if planner_task and planner_task.status in ("pending", "assigned"):
        result = _execute_single_task(db, planner_task)
        if result["status"] == "completed":
            tasks_completed += 1
            total_tokens += result.get("tokens_used", 0)
        elif result["status"] == "handoff":
            tasks_handoff += 1
            total_tokens += result.get("tokens_used", 0)
        else:
            tasks_failed += 1
        execution_log.append({
            "phase": "planning",
            "task_id": planner_task.id,
            "title": planner_task.title,
            "status": result["status"],
            "tokens_used": result.get("tokens_used", 0),
            "duration_ms": result.get("duration_ms", 0),
        })

    # Phase 2: Execute all pending execution tasks
    while True:
        task = _find_next_pending_task(db, goal_id)
        if not task:
            break
        result = _execute_single_task(db, task)
        if result["status"] == "completed":
            tasks_completed += 1
        elif result["status"] == "handoff":
            tasks_handoff += 1
        else:
            tasks_failed += 1
        total_tokens += result.get("tokens_used", 0)
        execution_log.append({
            "phase": "execution",
            "task_id": task.id,
            "title": task.title,
            "status": result["status"],
            "tokens_used": result.get("tokens_used", 0),
            "duration_ms": result.get("duration_ms", 0),
        })

    # Phase 3: Determine initial goal status
    db.refresh(goal)
    if tasks_handoff > 0:
        goal.status = "handoff"
    elif tasks_failed > 0 and tasks_completed == 0:
        goal.status = "failed"
    else:
        goal.status = "completed"
    goal.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Phase 4: Supervisor Review
    review_result = None
    run_id = f"run-{goal.id[:8]}"
    if goal.status == "completed" and tasks_completed > 0:
        try:
            from src.services import review_service as review_svc
            review_result = review_svc.generate_review(db, goal.id, run_id)
            total_tokens += review_result.get("tokens_used", 0)
        except Exception:
            pass

    # Phase 5: Memory Curation (after review passes)
    memory_result = None
    if review_result and review_result.get("passed"):
        try:
            from src.services import curator_service as curator_svc
            memory_result = curator_svc.generate_memories(db, goal.id, run_id)
        except Exception:
            pass

    total_elapsed = int((time.time() - start_time) * 1000)

    return {
        "goal_id": goal.id,
        "status": goal.status,
        "tasks_completed": tasks_completed,
        "tasks_failed": tasks_failed,
        "tasks_handoff": tasks_handoff,
        "total_tokens_used": total_tokens,
        "total_duration_ms": total_elapsed,
        "execution_log": execution_log,
        "review": review_result,
        "memory": memory_result,
    }


def execute_task_step(db: Session, task_id: str) -> Dict[str, Any]:
    """Execute a single task step."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise TaskNotReadyError(f"Task '{task_id}' not found")
    if task.status not in ("pending", "assigned"):
        raise TaskNotReadyError(f"Task must be pending or assigned, current: {task.status}")

    return _execute_single_task(db, task)


def _execute_single_task(db: Session, task: Task) -> Dict[str, Any]:
    """Internal: execute one task through model call -> logs -> quota."""
    provider = get_provider()
    start_ts = time.time()

    # 1. Assign task
    if task.status == "pending":
        task.status = "assigned"
        task.updated_at = datetime.now(timezone.utc)
        db.commit()

    # 2. Get agent
    agent = db.query(AgentStation).filter(
        AgentStation.id == task.assigned_agent_id,
        AgentStation.is_enabled == True,
    ).first()
    if not agent:
        raise TaskNotReadyError(f"Agent '{task.assigned_agent_id}' not found or disabled")

    # 3. Select model via Router
    task_type = ROLE_TO_TASK_TYPE.get(agent.role, "coding")
    routing = None
    try:
        routing = router_service.select_model(
            db=db,
            task_id=task.id,
            task_type=task_type,
            task_description=task.description or task.title,
            preferred_agent_id=agent.id,
        )
        selected_model_id = routing["selected_model_id"]
    except Exception:
        selected_model_id = agent.default_model_id

    # 4. Check quota
    intercept = quota_service.check_and_intercept(db, selected_model_id)
    if intercept and intercept.get("intercepted"):
        return _handle_quota_intercept(db, task, agent, selected_model_id, routing)

    # 5. Get model info
    model = db.query(Model).filter(Model.id == selected_model_id).first()
    model_name = model.display_name if model else selected_model_id

    # 6. Create WorkerSession
    worker = WorkerSession(
        id=str(uuid.uuid4()),
        agent_id=agent.id,
        model_id=selected_model_id,
        goal_id=task.goal_id,
        task_id=task.id,
        status="running",
        current_context=task.description or "",
    )
    db.add(worker)
    db.flush()
    task.assigned_worker_id = worker.id

    # 7. Transition: assigned -> running
    task.status = "running"
    task.updated_at = datetime.now(timezone.utc)
    if agent.status != "running":
        agent.status = "running"
        agent.current_task_id = task.id

    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "agent_id": agent.id,
        "worker_id": worker.id,
        "model_id": selected_model_id,
        "event_type": "agent_step",
        "event_status": "started",
        "input_summary": task.description or task.title,
        "metadata": {"task_type": task_type, "step": "execution"},
    })
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "agent_id": agent.id,
        "event_type": "task_status_change",
        "event_status": "transition",
        "output_summary": f"Task status: assigned -> running (agent: {agent.name}, model: {model_name})",
    })
    db.commit()

    # 8. Model call
    try:
        import asyncio
        provider = get_provider()
        messages = []
        if agent.system_prompt:
            messages.append({"role": "system", "content": agent.system_prompt})
        messages.append({"role": "user", "content": task.description or task.title})
        req = ModelRequest(
            provider=model.provider if model else "unknown",
            model=selected_model_id,
            messages=messages,
        )
        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(provider.generate(req))
        loop.close()
    except Exception as e:
        return _handle_task_failure(db, task, agent, worker, str(e))

    elapsed_ms = int((time.time() - start_ts) * 1000)
    latency_ms = response.latency_ms

    # 9. Log model_call
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "agent_id": agent.id,
        "worker_id": worker.id,
        "model_id": selected_model_id,
        "event_type": "model_call",
        "event_status": "completed",
        "input_summary": (task.description or task.title)[:200],
        "output_summary": response.content[:200],
        "token_usage": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
        },
        "latency_ms": latency_ms,
        "routing_info": {
            "routing_reason": routing.get("routing_reason", {}).get("summary", "") if routing else "",
            "confidence": routing.get("confidence", 0) if routing else 0,
        },
    })

    # 10. Record quota usage
    quota_result = quota_service.record_usage(
        db=db,
        provider=model.provider if model else "unknown",
        model_id=selected_model_id,
        model_name=model_name,
        request_tokens=response.input_tokens,
        response_tokens=response.output_tokens,
        total_tokens=response.total_tokens,
    )

    # 11. Update task
    task.status = "completed"
    task.output = response.content
    task.tokens_used = response.total_tokens
    task.duration_ms = elapsed_ms
    task.updated_at = datetime.now(timezone.utc)

    # 12. Update worker
    worker.status = "completed"
    worker.final_output = response.content
    worker.total_tokens_used = response.total_tokens
    worker.updated_at = datetime.now(timezone.utc)

    # 13. Update agent
    agent.status = "idle"
    agent.current_task_id = None
    agent.total_tasks_completed = (agent.total_tasks_completed or 0) + 1
    agent.updated_at = datetime.now(timezone.utc)

    # 14. Log completion
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "agent_id": agent.id,
        "worker_id": worker.id,
        "model_id": selected_model_id,
        "event_type": "agent_step",
        "event_status": "completed",
        "output_summary": response.content[:200],
        "token_usage": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
        },
        "latency_ms": latency_ms,
        "quota_status": quota_result.get("updated_status", "unknown") if quota_result else "unknown",
    })
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "agent_id": agent.id,
        "event_type": "task_status_change",
        "event_status": "transition",
        "output_summary": f"Task completed. Tokens: {response.total_tokens}, Duration: {elapsed_ms}ms",
    })
    db.commit()

    return {
        "task_id": task.id,
        "status": "completed",
        "output": response.content,
        "tokens_used": response.total_tokens,
        "duration_ms": elapsed_ms,
        "model_name": model_name,
        "worker_id": worker.id,
        "quota_status": quota_result.get("updated_status", "unknown") if quota_result else "unknown",
        "is_handoff": False,
    }


def _handle_task_failure(
    db: Session, task: Task, agent: AgentStation, worker: WorkerSession, error_msg: str
) -> Dict[str, Any]:
    task.status = "failed"
    task.updated_at = datetime.now(timezone.utc)
    agent.status = "idle"
    agent.current_task_id = None
    agent.total_tasks_failed = (agent.total_tasks_failed or 0) + 1
    agent.updated_at = datetime.now(timezone.utc)
    worker.status = "failed"
    worker.error_message = error_msg
    worker.updated_at = datetime.now(timezone.utc)
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "agent_id": agent.id,
        "worker_id": worker.id,
        "event_type": "error",
        "event_status": "failed",
        "error_message": error_msg,
        "error_type": "runtime_error",
    })
    db.commit()
    return {
        "task_id": task.id,
        "status": "failed",
        "output": None,
        "tokens_used": 0,
        "duration_ms": 0,
        "model_name": None,
        "worker_id": worker.id,
        "quota_status": None,
        "is_handoff": False,
    }


def _handle_quota_intercept(
    db: Session, task: Task, agent: AgentStation, model_id: str, routing: Dict
) -> Dict[str, Any]:
    """Handle intercepted model call by triggering handoff."""
    backup_model_ids = routing.get("backup_model_ids", []) if routing else []
    fallback_model_id = backup_model_ids[0] if backup_model_ids else agent.default_model_id

    # Find a target agent different from current
    target_agent = db.query(AgentStation).filter(
        AgentStation.id != agent.id,
        AgentStation.is_enabled == True,
    ).first()

    if not target_agent:
        task.status = "failed"
        task.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {
            "task_id": task.id,
            "status": "failed",
            "output": None,
            "tokens_used": 0,
            "duration_ms": 0,
            "model_name": None,
            "worker_id": None,
            "quota_status": "limited",
            "is_handoff": False,
        }

    # Create mirror HandoffTask for handoff service
    ht = HandoffTask(
        id=task.id,
        goal_id=task.goal_id,
        title=task.title,
        description=task.description or "",
        status="running",
        assigned_agent_id=agent.id,
        assigned_model_id=model_id,
        current_output=task.output or "",
    )
    db.add(ht)
    db.flush()

    try:
        result = handoff_service.trigger_handoff(
            db=db,
            task_id=task.id,
            to_agent_id=target_agent.id,
            to_model_id=fallback_model_id,
            reason="quota_exceeded",
            reason_description=f"Model {model_id} is in LIMITED/COOLDOWN status",
        )
    except handoff_service.HandoffServiceError:
        task.status = "failed"
        task.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {
            "task_id": task.id,
            "status": "failed",
            "output": None,
            "tokens_used": 0,
            "duration_ms": 0,
            "model_name": None,
            "worker_id": None,
            "quota_status": "limited",
            "is_handoff": False,
        }

    task.status = "handoff"
    task.updated_at = datetime.now(timezone.utc)
    agent.status = "handoff"
    agent.total_handoffs_initiated = (agent.total_handoffs_initiated or 0) + 1
    agent.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "task_id": task.id,
        "status": "handoff",
        "output": None,
        "tokens_used": 0,
        "duration_ms": 0,
        "model_name": model_id,
        "worker_id": None,
        "quota_status": "limited",
        "is_handoff": True,
    }


def _find_planner_task(db: Session, goal_id: str) -> Optional[Task]:
    planner_agents = db.query(AgentStation).filter(
        AgentStation.role == "planner",
        AgentStation.is_enabled == True,
    ).all()
    planner_ids = [a.id for a in planner_agents]
    if not planner_ids:
        return db.query(Task).filter(
            Task.goal_id == goal_id,
            Task.status.in_(["pending", "assigned"]),
        ).first()
    return db.query(Task).filter(
        Task.goal_id == goal_id,
        Task.assigned_agent_id.in_(planner_ids),
        Task.status.in_(["pending", "assigned"]),
    ).first()


def _find_next_pending_task(db: Session, goal_id: str) -> Optional[Task]:
    return db.query(Task).filter(
        Task.goal_id == goal_id,
        Task.status.in_(["pending", "assigned"]),
    ).order_by(Task.priority.desc(), Task.created_at.asc()).first()


def get_runtime_status(db: Session, goal_id: str) -> Dict[str, Any]:
    """Get the current runtime status for a goal by querying existing tables.

    No new table needed — aggregates from goals, tasks, worker_sessions,
    handoff_records, execution_logs, and quota_records.
    """
    goal = goal_service.get_goal(db, goal_id)

    tasks = db.query(Task).filter(Task.goal_id == goal_id).all()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "completed")
    failed_tasks = sum(1 for t in tasks if t.status == "failed")
    running_tasks = sum(1 for t in tasks if t.status == "running")
    handoff_tasks = sum(1 for t in tasks if t.status == "handoff")

    running_task = next((t for t in tasks if t.status == "running"), None)

    total_tokens_used = sum(t.tokens_used or 0 for t in tasks)

    handoff_count = db.query(HandoffRecord).filter(
        HandoffRecord.goal_id == goal_id
    ).count()

    log_count = db.query(ExecutionLog).filter(
        ExecutionLog.goal_id == goal_id
    ).count()

    model_call_count = db.query(ExecutionLog).filter(
        ExecutionLog.goal_id == goal_id,
        ExecutionLog.event_type == "model_call",
    ).count()

    error_count = db.query(ExecutionLog).filter(
        ExecutionLog.goal_id == goal_id,
        ExecutionLog.event_status.in_(["error", "failed"]),
    ).count()

    # Find final output from last completed task
    last_completed = db.query(Task).filter(
        Task.goal_id == goal_id,
        Task.status == "completed",
    ).order_by(Task.updated_at.desc()).first()
    final_output = last_completed.output if last_completed else None

    # Find any error message from failed tasks
    last_failed = db.query(Task).filter(
        Task.goal_id == goal_id,
        Task.status == "failed",
    ).first()
    error_message = last_failed.description if last_failed else None

    return {
        "goal_id": goal.id,
        "goal_title": goal.title,
        "goal_status": goal.status,
        "current_task_id": running_task.id if running_task else None,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "running_tasks": running_tasks,
        "handoff_tasks": handoff_tasks,
        "handoff_count": handoff_count,
        "total_tokens_used": total_tokens_used,
        "log_count": log_count,
        "model_call_count": model_call_count,
        "error_count": error_count,
        "final_output": final_output,
        "error_message": error_message,
        "quota_status": None,
    }
