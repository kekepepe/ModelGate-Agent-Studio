"""Runtime orchestrator: Goal -> Task -> Worker -> Model -> Logs -> Quota -> Handoff -> Output.

Orchestrates the full execution pipeline by stitching together existing
services from all 6 modules. Uses a mock model provider (swappable to
real OpenAI-compatible provider via the ModelProvider Protocol).
"""

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord, WorkerSession
from src.models.tool import ToolCallRecord
from src.models.model import Model
from src.models.workspace import Goal, RuntimeRun, Task
from src.models.workspace import Artifact, VerificationResult
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
from src.services.providers.base import ModelResponse


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

    run = _get_or_start_run(db, goal)
    start_time = time.time()
    total_tokens = 0
    tasks_completed = 0
    tasks_failed = 0
    tasks_handoff = 0
    execution_log: List[Dict[str, Any]] = []
    paused = False
    resource_limited = False

    if goal.status == "planning":
        goal.status = "running"
        goal.updated_at = datetime.now(timezone.utc)
        db.commit()

    # Execute only tasks whose dynamic dependencies have completed.  This
    # replaces the former hard-coded Planner -> Coder -> Reviewer chain.
    while True:
        db.refresh(goal)
        if goal.status == "paused":
            paused = True
            break
        resource_error = _run_resource_limit_error(db, run)
        if resource_error:
            resource_limited = True
            goal.status, run.status = "blocked", "blocked"
            log_service.create_log(db, {
                "goal_id": goal.id, "event_type": "run.resource_limit", "event_status": "blocked",
                "output_summary": resource_error,
                "metadata": {"budget_tokens": run.budget_tokens, "max_duration_seconds": run.max_duration_seconds},
            })
            db.commit()
            break
        from src.services.orchestrator_service import ready_tasks
        ready = ready_tasks(db, goal_id)
        task = ready[0] if ready else None
        if not task:
            break
        parallel = [item for item in ready if "parallel_safe" in item._get_json("required_capabilities")]
        if len(parallel) > 1:
            results = _execute_parallel_tasks(db, [item.id for item in parallel])
            db.expire_all()
            conflicted = _merge_parallel_worktrees(db, [item[0] for item in results])
            results = [(task_id, {**result, "status": "blocked"} if task_id in conflicted else result) for task_id, result in results]
            pairs = [(db.query(Task).filter(Task.id == item[0]).one(), item[1]) for item in results]
        else:
            pairs = [(task, _execute_single_task(db, task))]
        for executed_task, result in pairs:
            if result["status"] in ("completed", "completed_verified", "completed_unverified"):
                tasks_completed += 1
            elif result["status"] == "handoff":
                tasks_handoff += 1
            elif result["status"] != "pending":
                tasks_failed += 1
            total_tokens += result.get("tokens_used", 0)
            execution_log.append({
                "phase": "planning" if db.query(AgentStation).filter(AgentStation.id == executed_task.assigned_agent_id, AgentStation.role == "planner").first() else "parallel_execution" if len(parallel) > 1 else "execution",
                "task_id": executed_task.id,
                "title": executed_task.title,
                "status": result["status"],
                "tokens_used": result.get("tokens_used", 0),
                "duration_ms": result.get("duration_ms", 0),
            })

    # Phase 3: Determine initial goal status
    db.refresh(goal)
    if paused:
        # The request that paused a run has already persisted the Goal and Run
        # states. Do not overwrite it with a terminal status after the current
        # tool/model step has safely returned.
        goal.status = "paused"
    elif resource_limited:
        goal.status = "blocked"
    elif tasks_handoff > 0:
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
    db.refresh(goal)
    run.status = "completed" if goal.status == "completed" else goal.status
    if run.status == "completed":
        run.ended_at = datetime.now(timezone.utc)
        verified = db.query(Task).filter(Task.goal_id == goal.id, Task.task_type.in_(["coding", "verification"]), Task.status != "completed_verified").count() == 0
        run.final_verification_status = "passed" if verified else "unverified"
        goal.final_verification_status = run.final_verification_status
    db.commit()

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
        "run_id": run.id,
        "final_verification_status": run.final_verification_status,
    }


def _get_or_start_run(db: Session, goal: Goal) -> RuntimeRun:
    run = db.query(RuntimeRun).filter(RuntimeRun.id == goal.run_id).first() if goal.run_id else None
    if run and run.status in {"running", "paused"}:
        run.status = "running"
        return run
    run = RuntimeRun(
        id=str(uuid.uuid4()), goal_id=goal.id, execution_mode=goal.execution_mode, status="running",
        budget_tokens=goal.budget_tokens, budget_cost_usd=goal.budget_cost_usd,
        max_duration_seconds=goal.max_duration_seconds,
    )
    goal.run_id = run.id
    db.add(run)
    db.commit()
    log_service.create_log(db, {"goal_id": goal.id, "event_type": "run.created", "event_status": "completed", "output_summary": f"Run {run.id} started", "metadata": {"execution_mode": goal.execution_mode}})
    db.commit()
    return run


def _run_resource_limit_error(db: Session, run: RuntimeRun) -> Optional[str]:
    """Evaluate run-wide budgets before scheduling another Task."""
    used_tokens = db.query(func.coalesce(func.sum(Task.tokens_used), 0)).filter(
        Task.goal_id == run.goal_id
    ).scalar() or 0
    if run.budget_tokens and used_tokens >= run.budget_tokens:
        return f"Run token budget exhausted ({used_tokens}/{run.budget_tokens})"
    started_at = run.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    elapsed_seconds = (datetime.now(timezone.utc) - started_at).total_seconds()
    if run.max_duration_seconds and elapsed_seconds >= run.max_duration_seconds:
        return f"Run duration budget exhausted ({elapsed_seconds:.1f}s/{run.max_duration_seconds}s)"
    return None


def pause_goal_run(db: Session, goal_id: str) -> Dict[str, Any]:
    goal = goal_service.get_goal(db, goal_id)
    if goal.status not in {"planning", "running"} or not goal.run_id:
        raise GoalNotReadyError(f"Goal cannot be paused from status: {goal.status}")
    run = db.query(RuntimeRun).filter(RuntimeRun.id == goal.run_id).first()
    if not run:
        raise GoalNotReadyError("No active runtime run exists")
    goal.status, run.status = "paused", "paused"
    db.query(WorkerSession).filter(WorkerSession.goal_id == goal.id, WorkerSession.status == "running").update({"status": "paused"})
    db.commit()
    log_service.create_log(db, {"goal_id": goal.id, "event_type": "run.paused", "event_status": "completed", "output_summary": f"Run {run.id} paused"})
    db.commit()
    return {"goal_id": goal.id, "run_id": run.id, "status": "paused"}


def resume_goal_run(db: Session, goal_id: str) -> Dict[str, Any]:
    goal = goal_service.get_goal(db, goal_id)
    if goal.status != "paused" or not goal.run_id:
        raise GoalNotReadyError(f"Goal cannot be resumed from status: {goal.status}")
    run = db.query(RuntimeRun).filter(RuntimeRun.id == goal.run_id).first()
    if not run:
        raise GoalNotReadyError("No paused runtime run exists")
    goal.status, run.status = "running", "running"
    db.query(Task).filter(Task.goal_id == goal.id, Task.status == "running").update({"status": "pending"})
    db.query(WorkerSession).filter(WorkerSession.goal_id == goal.id, WorkerSession.status == "paused").update({"status": "idle"})
    db.commit()
    log_service.create_log(db, {"goal_id": goal.id, "event_type": "run.resumed", "event_status": "completed", "output_summary": f"Run {run.id} resumed"})
    db.commit()
    return {"goal_id": goal.id, "run_id": run.id, "status": "running"}


def _execute_parallel_tasks(db: Session, task_ids: List[str]) -> List[tuple[str, Dict[str, Any]]]:
    """Run independent Tasks in isolated DB sessions and worktrees."""
    factory = sessionmaker(bind=db.get_bind(), autocommit=False, autoflush=False)

    def run(task_id: str):
        worker_db = factory()
        try:
            task = worker_db.query(Task).filter(Task.id == task_id).one()
            return task_id, _execute_single_task(worker_db, task)
        finally:
            worker_db.close()

    with ThreadPoolExecutor(max_workers=len(task_ids), thread_name_prefix="modelgate-worker") as pool:
        futures = [pool.submit(run, task_id) for task_id in task_ids]
        return [future.result() for future in as_completed(futures)]


def _merge_parallel_worktrees(db: Session, task_ids: List[str]) -> set[str]:
    """Merge worker diffs serially; materialize conflicts as resolution work."""
    from src.models.workspace import WorkspaceWorktree
    from src.services.worktree_service import WorktreeError, merge_worktree
    conflicted = set()
    for task_id in task_ids:
        record = db.query(WorkspaceWorktree).filter(WorkspaceWorktree.task_id == task_id).first()
        if not record:
            continue
        result = merge_worktree(db, record)
        task = db.query(Task).filter(Task.id == task_id).one()
        log_service.create_log(db, {
            "goal_id": task.goal_id, "task_id": task.id, "event_type": "worktree_merged",
            "event_status": result["status"], "output_summary": result["message"],
            "metadata": {"worktree": record.path, "changed": result["changed"]},
        })
        if result["status"] == "conflict":
            conflicted.add(task.id)
            task.status = "blocked"
            task.blocked_reason = "Parallel worktree merge conflict"
            if not db.query(Task).filter(Task.parent_task_id == task.id, Task.title.like("Resolve conflict:%")).first():
                resolution = Task(
                    id=str(uuid.uuid4()), goal_id=task.goal_id, parent_task_id=task.id,
                    title=f"Resolve conflict: {task.title}",
                    description=f"Resolve the merge conflict retained in isolated worktree: {record.path}",
                    status="pending", assigned_agent_id=task.assigned_agent_id, priority=task.priority + 1,
                    task_type="coding", risk_level="high",
                )
                resolution.set_json("required_tools", task._get_json("required_tools"))
                resolution.set_json("required_capabilities", ["code_edit"])
                resolution.set_json("acceptance_criteria", task._get_json("acceptance_criteria"))
                db.add(resolution)
        db.commit()
    return conflicted


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


def _resource_limit_error(agent: AgentStation, total_tokens: int, start_ts: float) -> Optional[str]:
    """Return a visible failure reason before the worker exceeds its configured budget."""
    if total_tokens > (agent.max_tokens_per_task or 32000):
        return f"Agent token budget exceeded ({total_tokens}/{agent.max_tokens_per_task})"
    elapsed_seconds = time.time() - start_ts
    if elapsed_seconds > (agent.max_duration_seconds or 900):
        return f"Agent duration budget exceeded ({elapsed_seconds:.1f}s/{agent.max_duration_seconds}s)"
    return None


def _execute_single_task(db: Session, task: Task) -> Dict[str, Any]:
    """Internal: execute one task through model call -> logs -> quota."""
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

    # 6. Build traceable execution context before the worker starts. Handoff
    # context remains authoritative for a resumed worker; otherwise retrieve
    # only reviewed Memory/Skill entries.
    if not worker:
        goal = goal_service.get_goal(db, task.goal_id)
        from src.services.context_service import build_context_package
        context_package = build_context_package(db, goal, task)
        workspace_scope = None
        if "parallel_safe" in task._get_json("required_capabilities"):
            from src.services.worktree_service import create_worktree
            worktree = create_worktree(db, goal, task)
            workspace_scope = worktree.path
        worker = WorkerSession(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            model_id=selected_model_id,
            goal_id=task.goal_id,
            task_id=task.id,
            status="running",
            current_context=json.dumps(context_package, ensure_ascii=False),
            workspace_scope=workspace_scope,
        )
        db.add(worker)
        db.flush()
        task.assigned_worker_id = worker.id
        log_service.create_log(db, {
            "goal_id": task.goal_id, "task_id": task.id, "agent_id": agent.id, "worker_id": worker.id,
            "event_type": "memory_retrieved", "event_status": "completed",
            "output_summary": f"Retrieved {len(context_package['project_memories'])} memory item(s) and {len(context_package['skills'])} skill(s)",
            "metadata": {"memory_ids": [item["id"] for item in context_package["project_memories"]], "skill_ids": [item["id"] for item in context_package["skills"]]},
        })
        if workspace_scope:
            log_service.create_log(db, {
                "goal_id": task.goal_id, "task_id": task.id, "agent_id": agent.id, "worker_id": worker.id,
                "event_type": "worktree_created", "event_status": "completed",
                "output_summary": f"Isolated worktree created: {workspace_scope}",
            })

    # A selected real model must be usable before the agent transitions into
    # execution. Mock is explicitly offline/test-only and is intentionally
    # excluded from this network health check.
    execution_mode = goal_service.get_goal(db, task.goal_id).execution_mode
    if execution_mode != "mock":
        try:
            import asyncio
            provider = get_provider(model=model, execution_mode=execution_mode)
            health = asyncio.run(provider.health_check(model.model_name)) if hasattr(provider, "health_check") else {"healthy": True}
            log_service.create_log(db, {
                "goal_id": task.goal_id, "task_id": task.id, "agent_id": agent.id,
                "worker_id": worker.id, "model_id": selected_model_id,
                "event_type": "model_health", "event_status": "completed" if health.get("healthy") else "failed",
                "output_summary": health.get("message") or "Model health check completed",
                "metadata": health,
            })
            if not health.get("healthy"):
                return _handle_task_failure(db, task, agent, worker, health.get("message", "Selected model is unhealthy"), routing)
        except Exception as exc:
            return _handle_task_failure(db, task, agent, worker, f"Model health check failed: {exc}", routing)

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
    max_tool_loops = min(agent.max_tool_calls_per_task or 20, agent.max_steps_per_task or 10)
    total_input_tokens = 0
    total_output_tokens = 0
    final_content = ""
    tool_call_count = 0
    repeated_tool_signatures = set()
    consecutive_tool_failures = worker.failure_count or 0

    try:
        import asyncio
        messages = []
        if agent.system_prompt:
            messages.append({"role": "system", "content": agent.system_prompt})
        if worker.current_context:
            messages.append({"role": "system", "content": f"Verified execution context:\n{worker.current_context}"})
        messages.append({"role": "user", "content": task.description or task.title})

        for _ in range(max_tool_loops + 1):
            limit_error = _resource_limit_error(agent, total_input_tokens + total_output_tokens, start_ts)
            if limit_error:
                raise RuntimeError(limit_error)
            provider = get_provider(model=model, execution_mode=goal_service.get_goal(db, task.goal_id).execution_mode)
            req = ModelRequest(
                provider=model.provider if model else "unknown",
                model=selected_model_id,
                messages=messages,
                tools=tools_payload,
                metadata={"provider_model_name": model.model_name if model else selected_model_id},
            )
            execution_mode = goal_service.get_goal(db, task.goal_id).execution_mode
            if not tools_payload and execution_mode != "mock" and hasattr(provider, "stream"):
                response = _stream_model_response(db, provider, req, task, worker, selected_model_id)
            else:
                response = asyncio.run(provider.generate(req))

            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens
            limit_error = _resource_limit_error(agent, total_input_tokens + total_output_tokens, start_ts)
            if limit_error:
                raise RuntimeError(limit_error)
            worker.step_count = (worker.step_count or 0) + 1
            worker.last_observation = (response.content or "tool call requested")[:4000]
            worker.next_action = "execute_tools" if response.finish_reason == "tool_calls" and response.tool_calls else "verify_completion"

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
                "metadata": {"provider": model.provider if model else "unknown", "provider_request_id": response.request_id},
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
                    signature = f"{tool_name}:{json.dumps(arguments, sort_keys=True, ensure_ascii=False)}"
                    if signature in repeated_tool_signatures:
                        raise RuntimeError(f"Repeated identical tool call detected: {tool_name}")
                    repeated_tool_signatures.add(signature)
                    try:
                        call_record = asyncio.run(executor.execute(
                                db=db, tool_name=tool_name, arguments=arguments,
                                goal_id=task.goal_id, task_id=task.id,
                                agent_id=agent.id, worker_id=worker.id,
                            ))
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
                        if call_record.status == "completed":
                            consecutive_tool_failures = 0
                            worker.failure_count = 0
                        else:
                            consecutive_tool_failures += 1
                            worker.failure_count = consecutive_tool_failures
                            if consecutive_tool_failures >= (agent.max_consecutive_failures or 3):
                                raise RuntimeError(
                                    f"Agent consecutive tool failure limit exceeded "
                                    f"({consecutive_tool_failures}/{agent.max_consecutive_failures})"
                                )
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

    # 11. Evidence-based completion. A code task with a contract can never be
    # promoted by a model sentence alone.
    verification = _verify_task(db, task)
    task.verification_status = verification["status"]
    if verification["status"] == "passed":
        task.status = "completed_verified"
    elif task.retry_count < task.max_retries and task.task_type in {"coding", "verification"}:
        task.retry_count += 1
        task.status = "pending"
        task.blocked_reason = "Verification failed; retrying with recorded evidence."
        final_content = f"{final_content}\n\n[Verification failed; retry {task.retry_count}/{task.max_retries} scheduled.]"
    elif task.task_type in {"general", "direct", "planning", "research", "summarization", "review"}:
        # Subjective/direct work has no executable contract by design. It is
        # explicitly visible as unverified rather than being blocked or
        # promoted to verified completion.
        task.status = "completed" if task.task_type == "general" else "completed_unverified"
    elif goal_service.get_goal(db, task.goal_id).execution_mode == "mock":
        # Explicit Mock is retained for offline/demo regression only. It can
        # never claim verification, but it must keep the legacy presentation
        # flow runnable without faking a Live success.
        task.status = "completed_unverified"
        task.blocked_reason = "Mock execution cannot supply real verification evidence."
    else:
        # Code and verification work may not be presented as complete merely
        # because the model exhausted its retry budget. Restore the latest
        # stable state for each changed path and leave an actionable block.
        restored = _restore_task_checkpoints(db, task)
        task.status = "blocked"
        task.blocked_reason = (
            "Verification failed after retry budget; restored latest checkpoints: "
            + (", ".join(restored) if restored else "none available")
        )
    task.output = final_content
    task.tokens_used = total_tokens
    task.duration_ms = elapsed_ms
    task.updated_at = datetime.now(timezone.utc)

    # 12. Update worker
    worker.status = "completed" if task.status != "pending" else "failed"
    worker.final_output = final_content
    worker.total_tokens_used = total_tokens
    worker.next_action = "retry" if task.status == "pending" else "completed" if task.status.startswith("completed") else "blocked"
    from src.services import curator_service
    curator_service.record_skill_outcome(db, worker.current_context, task.status == "completed_verified")
    worker.updated_at = datetime.now(timezone.utc)

    # 13. Update agent
    agent.status = "idle"
    agent.current_task_id = None
    if task.status == "pending":
        agent.total_tasks_failed = (agent.total_tasks_failed or 0) + 1
    else:
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
        "output_summary": f"Task {task.status}. Tokens: {total_tokens}, Duration: {elapsed_ms}ms, Tool calls: {tool_call_count}",
    })
    db.commit()

    return {
        "task_id": task.id,
        "status": task.status,
        "output": final_content,
        "tokens_used": total_tokens,
        "duration_ms": elapsed_ms,
        "model_name": model_name,
        "worker_id": worker.id,
        "quota_status": quota_result.get("updated_status", "unknown") if quota_result else "unknown",
        "is_handoff": False,
        "tool_call_count": tool_call_count,
        "verification": verification,
    }


def _stream_model_response(db: Session, provider, request: ModelRequest, task: Task, worker: WorkerSession, model_id: str) -> ModelResponse:
    """Persist real token chunks for tool-free tasks without fabricating them."""
    import asyncio
    import time

    async def collect():
        chunks, request_id = [], None
        async for event in provider.stream(request):
            request_id = event.request_id or request_id
            if event.type == "token" and event.content:
                chunks.append(event.content)
                log_service.create_log(db, {
                    "goal_id": task.goal_id, "task_id": task.id, "agent_id": worker.agent_id,
                    "worker_id": worker.id, "model_id": model_id, "event_type": "model_stream",
                    "event_status": "running", "output_summary": event.content[:200],
                    "metadata": {"provider_request_id": request_id},
                })
        return "".join(chunks), request_id

    started = time.time()
    content, request_id = asyncio.run(collect())
    return ModelResponse(
        content=content, input_tokens=0, output_tokens=0, total_tokens=0,
        latency_ms=int((time.time() - started) * 1000), request_id=request_id,
    )


def _restore_task_checkpoints(db: Session, task: Task) -> List[str]:
    """Restore one latest checkpoint per path after an unrecoverable failure."""
    import os
    from src.models.workspace import WorkspaceCheckpoint

    checkpoints = db.query(WorkspaceCheckpoint).filter(
        WorkspaceCheckpoint.goal_id == task.goal_id,
        WorkspaceCheckpoint.task_id == task.id,
    ).order_by(WorkspaceCheckpoint.created_at.desc()).all()
    restored, seen = [], set()
    for checkpoint in checkpoints:
        if checkpoint.path in seen:
            continue
        seen.add(checkpoint.path)
        try:
            if checkpoint.existed:
                os.makedirs(os.path.dirname(checkpoint.path), exist_ok=True)
                with open(checkpoint.path, "w", encoding="utf-8") as handle:
                    handle.write(checkpoint.content or "")
            elif os.path.exists(checkpoint.path):
                os.remove(checkpoint.path)
            restored.append(checkpoint.path)
        except OSError:
            continue
    if restored:
        log_service.create_log(db, {
            "goal_id": task.goal_id, "task_id": task.id,
            "event_type": "checkpoint_restored", "event_status": "completed",
            "output_summary": f"Restored {len(restored)} checkpointed path(s) after verification failure",
            "metadata": {"paths": restored},
        })
    return restored


def _verify_task(db: Session, task: Task) -> Dict[str, Any]:
    """Evaluate the persisted Completion Contract and retain its evidence."""
    criteria = task._get_json("acceptance_criteria")
    if not criteria:
        return {"status": "unverified", "results": []}
    results = []
    all_passed = True
    artifacts = db.query(Artifact).filter(Artifact.task_id == task.id).all()
    for criterion in criteria:
        kind = criterion.get("type") if isinstance(criterion, dict) else "unknown"
        if kind == "diff_exists":
            passed = bool(artifacts)
            evidence = f"{len(artifacts)} tracked changed file(s)"
            command = "artifact_register"
        elif kind == "file_exists":
            import os
            root = goal_service.get_goal(db, task.goal_id).workspace_root or "."
            target = os.path.realpath(os.path.join(root, criterion.get("target", "")))
            passed = target.startswith(os.path.realpath(root) + os.sep) and os.path.isfile(target)
            evidence, command = target, "file_exists"
        elif kind in {"tests_pass", "lint_pass", "typecheck_pass", "build_pass"}:
            latest_change = max((item.created_at for item in artifacts), default=None)
            required_tool = {
                "tests_pass": "test_runner", "lint_pass": "lint_run",
                "typecheck_pass": "typecheck_run", "build_pass": "build_run",
            }[kind]
            query = db.query(ToolCallRecord).filter(
                ToolCallRecord.task_id == task.id,
                # A generic shell command is evidence of observation, not of
                # a named verification step. Completion contracts require the
                # dedicated tool so a model cannot satisfy them with `exit(0)`.
                ToolCallRecord.tool_name == required_tool,
                ToolCallRecord.status == "completed",
            )
            if latest_change:
                query = query.filter(ToolCallRecord.created_at >= latest_change)
            successful_run = query.order_by(ToolCallRecord.created_at.desc()).first()
            passed = successful_run is not None
            evidence = successful_run.tool_output[:1000] if successful_run and successful_run.tool_output else f"No successful {required_tool} command after the latest change"
            command = successful_run.get_tool_input().get("command", required_tool) if successful_run else required_tool
        elif kind == "review_score":
            from src.models.supervisor import SupervisorReview
            review = db.query(SupervisorReview).filter(SupervisorReview.goal_id == task.goal_id).order_by(SupervisorReview.created_at.desc()).first()
            score = 1.0 if review and review.passed else 0.0
            minimum = float(criterion.get("minimum", 0.8))
            passed = score >= minimum
            evidence, command = f"Supervisor score proxy={score:.1f}; minimum={minimum:.2f}", "supervisor_review"
        else:
            passed, evidence, command = False, "Unsupported verification criterion", str(criterion)
        result = VerificationResult(task_id=task.id, criterion_type=kind, command_or_rule=command,
                                    status="passed" if passed else "failed", evidence=evidence, exit_code=0 if passed else 1)
        db.add(result)
        results.append({"type": kind, "status": result.status, "evidence": evidence})
        all_passed = all_passed and passed
    return {"status": "passed" if all_passed else "failed", "results": results}


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
            worker.failure_count = (worker.failure_count or 0) + 1
            worker.next_action = "handoff"
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
    worker.failure_count = (worker.failure_count or 0) + 1
    worker.next_action = "failed"
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
    completed_tasks = sum(1 for t in tasks if t.status in ("completed", "completed_verified", "completed_unverified"))
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
        Task.status.in_(["completed", "completed_verified", "completed_unverified"]),
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

    terminal_success = {"completed", "completed_verified", "completed_unverified"}
    completed = [task for task in tasks if task.status in terminal_success]
    incomplete = [task for task in tasks if task.status not in terminal_success]
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
