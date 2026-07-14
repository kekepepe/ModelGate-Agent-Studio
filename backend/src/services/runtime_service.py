"""Runtime orchestrator: Goal -> Task -> Worker -> Model -> Logs -> Quota -> Handoff -> Output.

Orchestrates the full execution pipeline by stitching together existing
services from all 6 modules. Uses a mock model provider (swappable to
real OpenAI-compatible provider via the ModelProvider Protocol).
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord, WorkerSession
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
    resumed_worker = None
    if task.assigned_worker_id:
        resumed_worker = db.query(WorkerSession).filter(WorkerSession.id == task.assigned_worker_id).first()
    can_resume_handoff = bool(
        task.status == "running"
        and resumed_worker
        and resumed_worker.inherited_from_handoff_id
        and resumed_worker.status == "running"
    )
    if task.status not in ("pending", "assigned") and not can_resume_handoff:
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

    # 3. Resume an accepted Handoff with its chosen model and inherited context.
    # For ordinary tasks, compute a new routing decision as before.
    worker = None
    resumed_from_handoff = False
    task_type = ROLE_TO_TASK_TYPE.get(agent.role, "coding")
    if task.assigned_worker_id:
        existing_worker = db.query(WorkerSession).filter(WorkerSession.id == task.assigned_worker_id).first()
        if existing_worker and existing_worker.inherited_from_handoff_id and existing_worker.status == "running":
            worker = existing_worker
            resumed_from_handoff = True

    routing = None
    if resumed_from_handoff:
        selected_model_id = worker.model_id
        routing = {
            "selected_model_id": selected_model_id,
            "routing_reason": {"summary": "沿用 Handoff 已确认的接手模型"},
            "confidence": 1.0,
            "backup_model_ids": [],
            "risk_flags": [],
            "score_breakdown": [],
            "is_user_override": False,
        }
    else:
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

    # 4. Check quota. A proactive Router fallback keeps a model out of the
    # candidate list, but an Agent whose configured primary model is blocked
    # still needs a visible continuity decision rather than a silent swap.
    # That decision is represented as an automatic Handoff in Workspace.
    default_intercept = quota_service.check_and_intercept(db, agent.default_model_id)
    if (
        not resumed_from_handoff
        and
        selected_model_id != agent.default_model_id
        and default_intercept
        and default_intercept.get("intercepted")
    ):
        return _handle_quota_intercept(db, task, agent, agent.default_model_id, routing)

    intercept = quota_service.check_and_intercept(db, selected_model_id)
    if intercept and intercept.get("intercepted"):
        return _handle_quota_intercept(db, task, agent, selected_model_id, routing)

    # 5. Get model info
    model = db.query(Model).filter(Model.id == selected_model_id).first()
    model_name = model.display_name if model else selected_model_id

    # 6. Create WorkerSession
    if not worker:
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

    # 8. Build tools from agent.allowed_tools
    allowed_tool_names = agent.get_allowed_tools() if agent else []
    tools_payload = None
    if allowed_tool_names:
        from src.models.tool import ToolDefinition as ToolDefORM
        from src.services.tool_service import BUILTIN_TOOLS
        tool_defs = db.query(ToolDefORM).filter(
            ToolDefORM.name.in_(allowed_tool_names),
            ToolDefORM.is_enabled == True,
        ).all()
        tools_payload = []
        for td in tool_defs:
            params = td.get_parameters()
            tools_payload.append({
                "type": "function",
                "function": {
                    "name": td.name,
                    "description": td.description,
                    "parameters": params,
                },
            })

    # 9. Model call with tool-call loop
    max_tool_loops = agent.max_tool_calls_per_task or 20
    total_input_tokens = 0
    total_output_tokens = 0
    final_content = ""
    tool_call_count = 0

    try:
        import asyncio
        provider = get_provider()
        messages = []
        if agent.system_prompt:
            messages.append({"role": "system", "content": agent.system_prompt})
        messages.append({"role": "user", "content": task.description or task.title})

        for _ in range(max_tool_loops + 1):
            req = ModelRequest(
                provider=model.provider if model else "unknown",
                model=selected_model_id,
                messages=messages,
                tools=tools_payload,
            )
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(provider.generate(req))
            loop.close()

            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens

            # Log model_call
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
                "latency_ms": response.latency_ms,
                # Keep the full decision beside the model call so Workspace can explain
                # the selected model without issuing a second routing request.
                "routing_info": routing or {
                    "selected_model_id": selected_model_id,
                    "routing_reason": {"summary": "使用 Agent 默认模型（路由不可用）"},
                    "confidence": 0,
                    "backup_model_ids": [],
                    "risk_flags": [],
                    "score_breakdown": [],
                    "is_user_override": False,
                },
            })

            if response.finish_reason == "tool_calls" and response.tool_calls:
                from src.services.tool_service import ToolExecutor, ToolNotAllowedError, ToolNotFoundError
                executor = ToolExecutor()
                messages.append({"role": "assistant", "content": response.content or "", "tool_calls": response.tool_calls})
                for tc in response.tool_calls:
                    func = tc.get("function", {})
                    tool_name = func.get("name", "")
                    try:
                        arguments = json.loads(func.get("arguments", "{}"))
                    except (json.JSONDecodeError, TypeError):
                        arguments = {}
                    try:
                        call_record = loop.run_until_complete(
                            executor.execute(
                                db=db, tool_name=tool_name, arguments=arguments,
                                goal_id=task.goal_id, task_id=task.id,
                                agent_id=agent.id, worker_id=worker.id,
                            )
                        )
                        tool_result = call_record.tool_output or ""
                    except (ToolNotAllowedError, ToolNotFoundError) as e:
                        call_record = None
                        tool_result = f"Error: {str(e)}"
                        log_service.create_log(db, {
                            "goal_id": task.goal_id,
                            "task_id": task.id,
                            "agent_id": agent.id,
                            "worker_id": worker.id,
                            "event_type": "tool_call",
                            "event_status": "failed",
                            "tool_name": tool_name,
                            "error_message": str(e),
                        })
                    if call_record:
                        log_service.create_log(db, {
                            "goal_id": task.goal_id,
                            "task_id": task.id,
                            "agent_id": agent.id,
                            "worker_id": worker.id,
                            "event_type": "tool_call",
                            "event_status": call_record.status,
                            "tool_name": tool_name,
                            "output_summary": (call_record.tool_output or "")[:200],
                            "latency_ms": call_record.latency_ms,
                            "error_message": call_record.error_message,
                        })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", str(uuid.uuid4())),
                        "content": tool_result,
                    })
                    tool_call_count += 1
            else:
                final_content = response.content
                break
    except Exception as e:
        return _handle_task_failure(db, task, agent, worker, str(e), routing)

    # 10. Record quota usage
    total_tokens = total_input_tokens + total_output_tokens
    quota_result = quota_service.record_usage(
        db=db,
        provider=model.provider if model else "unknown",
        model_id=selected_model_id,
        model_name=model_name,
        request_tokens=total_input_tokens,
        response_tokens=total_output_tokens,
        total_tokens=total_tokens,
    )

    elapsed_ms = int((time.time() - start_ts) * 1000)

    # 11. Update task
    task.status = "completed"
    task.output = final_content
    task.tokens_used = total_tokens
    task.duration_ms = elapsed_ms
    task.updated_at = datetime.now(timezone.utc)

    # 12. Update worker
    worker.status = "completed"
    worker.final_output = final_content
    worker.total_tokens_used = total_tokens
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
        "output_summary": final_content[:200],
        "token_usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
        },
        "latency_ms": elapsed_ms,
        "quota_status": quota_result.get("updated_status", "unknown") if quota_result else "unknown",
        "metadata": {"tool_call_count": tool_call_count},
    })
    log_service.create_log(db, {
        "goal_id": task.goal_id,
        "task_id": task.id,
        "agent_id": agent.id,
        "event_type": "task_status_change",
        "event_status": "transition",
        "output_summary": f"Task completed. Tokens: {total_tokens}, Duration: {elapsed_ms}ms, Tool calls: {tool_call_count}",
    })
    db.commit()

    return {
        "task_id": task.id,
        "status": "completed",
        "output": final_content,
        "tokens_used": total_tokens,
        "duration_ms": elapsed_ms,
        "model_name": model_name,
        "worker_id": worker.id,
        "quota_status": quota_result.get("updated_status", "unknown") if quota_result else "unknown",
        "is_handoff": False,
        "tool_call_count": tool_call_count,
    }


def _handle_task_failure(
    db: Session, task: Task, agent: AgentStation, worker: WorkerSession, error_msg: str, routing: Optional[Dict] = None,
) -> Dict[str, Any]:
    backup_model_ids = routing.get("backup_model_ids", []) if routing else []
    target_agent = db.query(AgentStation).filter(
        AgentStation.id != agent.id,
        AgentStation.is_enabled == True,
    ).first()
    if backup_model_ids and target_agent:
        try:
            handoff_result = handoff_service.trigger_handoff(
                db=db,
                task_id=task.id,
                to_agent_id=target_agent.id,
                to_model_id=backup_model_ids[0],
                reason="error",
                reason_description=f"Provider execution failed: {error_msg}",
            )
            worker.status = "failed"
            worker.error_message = error_msg
            worker.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "task_id": task.id,
                "status": "handoff",
                "output": None,
                "tokens_used": 0,
                "duration_ms": 0,
                "model_name": None,
                "worker_id": worker.id,
                "quota_status": None,
                "is_handoff": True,
                "handoff_id": handoff_result["handoff_id"],
            }
        except handoff_service.HandoffServiceError:
            # Preserve the original execution error below if automatic recovery
            # cannot create a valid continuation path.
            pass

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
    final_summary = _build_final_summary(db, goal, tasks, handoff_count)

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
        "final_summary": final_summary,
    }


def _build_final_summary(
    db: Session,
    goal: Goal,
    tasks: List[Task],
    handoff_count: int,
) -> Dict[str, Any]:
    """Build an honest, inspectable completion report for the Workspace.

    Model records currently expose a relative ``cost_level`` but not provider
    currency pricing. The report therefore explicitly marks a currency
    estimate unavailable instead of inventing a monetary value.
    """
    from src.services import review_service

    completed = [task for task in tasks if task.status == "completed"]
    incomplete = [task for task in tasks if task.status != "completed"]
    review = review_service.get_review(db, goal.id)

    logs = (
        db.query(ExecutionLog)
        .filter(ExecutionLog.goal_id == goal.id, ExecutionLog.model_id.isnot(None))
        .order_by(ExecutionLog.created_at.asc())
        .all()
    )
    model_ids = list(dict.fromkeys(log.model_id for log in logs if log.model_id))
    models_by_id = {}
    if model_ids:
        models_by_id = {
            model.id: model
            for model in db.query(Model).filter(Model.id.in_(model_ids)).all()
        }

    model_usage = [
        {
            "id": model_id,
            "name": models_by_id[model_id].display_name if model_id in models_by_id else model_id,
            "cost_level": models_by_id[model_id].cost_level if model_id in models_by_id else None,
        }
        for model_id in model_ids
    ]
    issues = review.get("issues", []) if review else []
    risks = list(issues)
    if incomplete:
        risks.append(f"仍有 {len(incomplete)} 个 Task 未完成")
    if handoff_count:
        risks.append(f"执行期间发生 {handoff_count} 次 Handoff")

    return {
        "completed": [task.title for task in completed],
        "incomplete": [task.title for task in incomplete],
        "quality": {
            "status": review.get("status") if review else "not_available",
            "passed": review.get("passed") if review else None,
            "summary": review.get("summary") if review else None,
            "reviewer_model_id": review.get("reviewer_model_id") if review else None,
        },
        "risks": risks,
        "models": model_usage,
        "handoff_count": handoff_count,
        "cost": {
            "currency_estimate": None,
            "available": False,
            "note": "尚未配置 Provider 单价表；当前只展示模型相对 cost_level，不虚构货币成本。",
        },
    }
