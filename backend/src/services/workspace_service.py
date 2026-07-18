from typing import Dict, List

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord, WorkerSession
from src.models.model import Model
from src.models.quota import QuotaRecord
from src.models.workspace import Goal, Task
from src.models.workspace import Artifact, ExecutionPlan, PlanChange, PlanTask, VerificationResult
from src.models.tool import ToolCallRecord
from src.models.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeSource, RetrievalRun, RetrievedContextItem
from src.models.selection import AgentSelectionDecision


class WorkspaceNotFoundError(Exception):
    pass


def get_workspace_state(db: Session, goal_id: str) -> Dict:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise WorkspaceNotFoundError(f"Goal '{goal_id}' not found")

    # Return the persisted graph order; dependencies remain available on each
    # task so the UI can distinguish waiting from actively running work.
    tasks = (
        db.query(Task)
        .filter(Task.goal_id == goal_id)
        .order_by(Task.created_at.asc(), Task.id.asc())
        .all()
    )

    # All registered agents
    agents = db.query(AgentStation).filter(AgentStation.is_enabled == True).all()

    # Workers related to this goal
    workers = db.query(WorkerSession).filter(WorkerSession.goal_id == goal_id).all()
    handoff_records = (
        db.query(HandoffRecord)
        .filter(HandoffRecord.goal_id == goal_id)
        .order_by(HandoffRecord.created_at.asc())
        .all()
    )
    plans = (
        db.query(ExecutionPlan)
        .filter(ExecutionPlan.goal_id == goal_id)
        .order_by(ExecutionPlan.version.asc())
        .all()
    )
    active_plan = next((plan for plan in reversed(plans) if plan.status == "active"), None)
    active_plan_tasks = (
        db.query(PlanTask)
        .filter(PlanTask.plan_version_id == active_plan.id)
        .order_by(PlanTask.created_at.asc(), PlanTask.client_task_id.asc())
        .all()
        if active_plan else []
    )
    plan_changes = (
        db.query(PlanChange)
        .filter(PlanChange.goal_id == goal_id)
        .order_by(PlanChange.created_at.asc())
        .all()
    )
    retrieval_runs = db.query(RetrievalRun).filter(
        RetrievalRun.goal_id == goal_id
    ).order_by(RetrievalRun.created_at.asc()).all()
    retrieval_payload = _serialize_retrieval_runs(db, retrieval_runs)
    retrieval_by_task: Dict[str, List[Dict]] = {}
    for run in retrieval_payload:
        if run["task_id"]:
            retrieval_by_task.setdefault(run["task_id"], []).append(run)

    task_ids = {task.id for task in tasks}
    artifacts_by_task: Dict[str, List[Artifact]] = {}
    verification_by_task: Dict[str, List[VerificationResult]] = {}
    tools_by_task: Dict[str, List[ToolCallRecord]] = {}
    if task_ids:
        for artifact in db.query(Artifact).filter(Artifact.task_id.in_(task_ids)).order_by(Artifact.created_at.asc()).all():
            artifacts_by_task.setdefault(artifact.task_id, []).append(artifact)
        for verification in db.query(VerificationResult).filter(VerificationResult.task_id.in_(task_ids)).order_by(VerificationResult.created_at.asc()).all():
            verification_by_task.setdefault(verification.task_id, []).append(verification)
        for call in db.query(ToolCallRecord).filter(ToolCallRecord.task_id.in_(task_ids)).order_by(ToolCallRecord.created_at.desc()).all():
            if len(tools_by_task.setdefault(call.task_id, [])) < 6:
                tools_by_task[call.task_id].append(call)
    recent_logs = []
    if task_ids:
        # One bounded query feeds the task detail panels and avoids a polling
        # waterfall of /logs and /router requests for every visible card.
        recent_logs = (
            db.query(ExecutionLog)
            .filter(ExecutionLog.task_id.in_(task_ids))
            .order_by(ExecutionLog.created_at.desc())
            .limit(max(len(task_ids) * 12, 12))
            .all()
        )

    latest_worker_by_task: Dict[str, WorkerSession] = {}
    for worker in workers:
        existing = latest_worker_by_task.get(worker.task_id)
        if not existing or (worker.created_at and existing.created_at and worker.created_at > existing.created_at):
            latest_worker_by_task[worker.task_id] = worker

    model_ids = {w.model_id for w in workers if w.model_id}
    models = {}
    if model_ids:
        db_models = db.query(Model).filter(Model.id.in_(model_ids)).all()
        models = {m.id: m.display_name for m in db_models}

    quota_by_model = {}
    if model_ids:
        quota_records = db.query(QuotaRecord).filter(QuotaRecord.model_id.in_(model_ids)).all()
        quota_by_model = {record.model_id: _serialize_quota(record) for record in quota_records}

    logs_by_task: Dict[str, List[ExecutionLog]] = {}
    for log in recent_logs:
        if log.task_id and len(logs_by_task.setdefault(log.task_id, [])) < 10:
            logs_by_task[log.task_id].append(log)

    agent_labels = {a.id: {"name": a.name, "role": a.role} for a in agents}
    handoffs = [_serialize_workspace_handoff(record, agent_labels) for record in handoff_records]
    handoffs_by_task: Dict[str, List[Dict]] = {}
    for handoff in handoffs:
        handoffs_by_task.setdefault(handoff["task_id"], []).append(handoff)

    selection_decisions = [item.to_dict() for item in db.query(AgentSelectionDecision).filter(
        AgentSelectionDecision.goal_id == goal_id,
    ).order_by(AgentSelectionDecision.created_at.asc()).all()]
    selection_by_plan_task = {item["task_id"]: item for item in selection_decisions}

    task_data = []
    for flow_position, task in enumerate(tasks, start=1):
        item = task.to_dict()
        item["flow_position"] = flow_position
        timeline = handoffs_by_task.get(task.id, [])
        worker = latest_worker_by_task.get(task.id)
        task_logs = logs_by_task.get(task.id, [])
        routing_decision = next(
            (log.get_routing_info() for log in task_logs if log.get_routing_info()),
            None,
        )
        item["handoffs"] = timeline
        item["handoff"] = timeline[-1] if timeline else None
        item["worker_status"] = worker.status if worker else None
        item["model_id"] = worker.model_id if worker else None
        item["model_name"] = models.get(worker.model_id) if worker else None
        item["quota"] = quota_by_model.get(worker.model_id) if worker else None
        item["routing_decision"] = routing_decision
        item["selection_decision"] = selection_by_plan_task.get(task.plan_task_id)
        item["context"] = worker.current_context if worker else None
        item["recent_logs"] = [_serialize_workspace_log(log, models, agent_labels) for log in task_logs]
        artifacts = artifacts_by_task.get(task.id, [])
        verifications = verification_by_task.get(task.id, [])
        tool_calls = tools_by_task.get(task.id, [])
        item["artifacts"] = [_serialize_artifact(artifact) for artifact in artifacts]
        item["verification_results"] = [_serialize_verification(verification) for verification in verifications]
        item["context_runs"] = retrieval_by_task.get(task.id, [])
        item["recent_tool_calls"] = [_serialize_tool_call(call) for call in tool_calls]
        item["latest_tool_call"] = item["recent_tool_calls"][0] if item["recent_tool_calls"] else None
        item["changed_files"] = sorted({path for call in tool_calls for path in call.get_result().get("changed_files", [])})
        latest_test = next((call for call in tool_calls if call.tool_name in {"test_runner", "lint_run", "typecheck_run", "build_run"}), None)
        item["test_status"] = latest_test.status if latest_test else None
        task_data.append(item)

    runtime_id_by_client = {
        task.client_task_id: task.runtime_task_id
        for task in active_plan_tasks
        if task.runtime_task_id
    }
    task_edges = [
        {
            "source": runtime_id_by_client[dependency],
            "target": task.runtime_task_id,
            "source_client_task_id": dependency,
            "target_client_task_id": task.client_task_id,
        }
        for task in active_plan_tasks
        if task.runtime_task_id
        for dependency in task._get_json("dependencies")
        if dependency in runtime_id_by_client
    ]
    parallel_task_ids = [
        task.runtime_task_id for task in active_plan_tasks
        if task.parallel_safe and task.runtime_task_id
    ]
    from src.services import verifier_service
    completion_evidence = verifier_service.evaluate_goal_completion(db, goal, emit_event=False)
    from src.services import multi_agent_metrics_service
    multi_agent_metrics = multi_agent_metrics_service.calculate(active_plan, active_plan_tasks, tasks)

    return {
        "goal": goal.to_dict() if goal else None,
        "tasks": task_data,
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role,
                "status": a.status,
                "default_model_id": a.default_model_id,
                "is_enabled": a.is_enabled,
            }
            for a in agents
        ],
        "workers": [
            {
                "id": w.id,
                "agent_id": w.agent_id,
                "model_id": w.model_id,
                "goal_id": w.goal_id,
                "task_id": w.task_id,
                "inherited_from_handoff_id": w.inherited_from_handoff_id,
                "status": w.status,
                "total_tokens_used": w.total_tokens_used,
                "workspace_scope": w.workspace_scope,
                "step_count": w.step_count,
                "failure_count": w.failure_count,
                "last_observation": w.last_observation,
                "next_action": w.next_action,
                "model_name": models.get(w.model_id) if w.model_id else None,
            }
            for w in workers
        ],
        "handoffs": handoffs,
        "active_plan": active_plan.to_dict(active_plan_tasks) if active_plan else None,
        "plan_versions": [
            {
                "id": plan.id,
                "plan_id": plan.plan_id,
                "version": plan.version,
                "status": plan.status,
                "task_mode": plan.task_mode,
                "activation_reason": plan.activation_reason,
                "planner_type": plan.planner_type,
                "created_at": plan.created_at.isoformat() if plan.created_at else None,
            }
            for plan in plans
        ],
        "task_mode": active_plan.task_mode if active_plan else None,
        "activation_reason": active_plan.activation_reason if active_plan else None,
        "task_edges": task_edges,
        "parallel_groups": ([{"id": f"plan-v{active_plan.version}-parallel", "task_ids": parallel_task_ids}]
                            if active_plan and len(parallel_task_ids) >= 2 else []),
        "replan_events": [change.to_dict() for change in plan_changes if change.change_type == "replan"],
        "completion_evidence": completion_evidence,
        "context_runs": retrieval_payload,
        "selection_decisions": selection_decisions,
        "multi_agent_metrics": multi_agent_metrics,
    }


def _serialize_workspace_handoff(record: HandoffRecord, agent_labels: Dict[str, Dict[str, str]]) -> Dict:
    """A compact, task-oriented handoff timeline for the Workspace state payload."""
    from_agent = agent_labels.get(record.from_agent_id, {})
    to_agent = agent_labels.get(record.to_agent_id, {})
    return {
        "id": record.id,
        "task_id": record.task_id,
        "status": record.status,
        "reason": record.reason,
        "reason_description": record.reason_description,
        "from_agent_id": record.from_agent_id,
        "from_agent_name": from_agent.get("name"),
        "from_model_id": record.from_model_id,
        "to_agent_id": record.to_agent_id,
        "to_agent_name": to_agent.get("name"),
        "to_model_id": record.to_model_id,
        "result_after_handoff": record.result_after_handoff,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "accepted_at": record.accepted_at.isoformat() if record.accepted_at else None,
        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
    }


def _serialize_quota(record: QuotaRecord) -> Dict:
    return {
        "model_id": record.model_id,
        "quota_status": record.quota_status,
        "usage_percent": record.usage_percent,
        "estimated_remaining": record.estimated_remaining,
        "total_tokens": record.total_tokens,
        "token_limit": record.token_limit,
        "request_count": record.request_count,
    }


def _serialize_workspace_log(log: ExecutionLog, models: Dict[str, str], agent_labels: Dict[str, Dict[str, str]]) -> Dict:
    return {
        "id": log.id,
        "event_type": log.event_type,
        "event_status": log.event_status,
        "output_summary": log.output_summary,
        "input_summary": log.input_summary,
        "error_message": log.error_message,
        "quota_status": log.quota_status,
        "model_id": log.model_id,
        "model_name": models.get(log.model_id),
        "agent_id": log.agent_id,
        "agent_name": agent_labels.get(log.agent_id, {}).get("name"),
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _serialize_artifact(artifact: Artifact) -> Dict:
    return {
        "id": artifact.id, "type": artifact.type, "path": artifact.path,
        "checksum": artifact.checksum, "verification_status": artifact.verification_status,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
    }


def _serialize_verification(result: VerificationResult) -> Dict:
    return {
        "id": result.id, "criterion_type": result.criterion_type,
        "command_or_rule": result.command_or_rule, "status": result.status,
        "evidence": result.evidence, "exit_code": result.exit_code,
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


def _serialize_tool_call(call: ToolCallRecord) -> Dict:
    return {
        "id": call.id, "tool_name": call.tool_name, "status": call.status,
        "latency_ms": call.latency_ms, "error_message": call.error_message,
        "result": call.get_result(),
    }


def _serialize_retrieval_runs(db: Session, runs: List[RetrievalRun]) -> List[Dict]:
    if not runs:
        return []
    run_ids = [run.id for run in runs]
    items = db.query(RetrievedContextItem).filter(
        RetrievedContextItem.retrieval_run_id.in_(run_ids)
    ).order_by(RetrievedContextItem.retrieval_run_id.asc(), RetrievedContextItem.rank.asc()).all()
    chunk_ids = {item.chunk_id for item in items if item.chunk_id}
    chunks = {chunk.id: chunk for chunk in db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(chunk_ids)).all()} if chunk_ids else {}
    document_ids = {chunk.document_id for chunk in chunks.values()}
    documents = {doc.id: doc for doc in db.query(KnowledgeDocument).filter(KnowledgeDocument.id.in_(document_ids)).all()} if document_ids else {}
    source_ids = {item.source_id for item in items}
    sources = {source.id: source for source in db.query(KnowledgeSource).filter(KnowledgeSource.id.in_(source_ids)).all()} if source_ids else {}
    by_run: Dict[str, List[Dict]] = {}
    for item in items:
        chunk = chunks.get(item.chunk_id)
        document = documents.get(chunk.document_id) if chunk else None
        source = sources.get(item.source_id)
        by_run.setdefault(item.retrieval_run_id, []).append({
            "id": item.id, "rank": item.rank, "score": item.score, "used": item.used,
            "citation": item.citation, "token_count": item.token_count,
            "source_id": item.source_id, "source_name": source.name if source else None,
            "chunk_id": item.chunk_id, "path": document.path if document else None,
            "content": chunk.content if chunk else None,
        })
    return [{
        "id": run.id, "goal_id": run.goal_id, "task_id": run.task_id,
        "agent_id": run.agent_id, "query": run.query, "policy": run.policy,
        "filters": run.get_filters(), "latency_ms": run.latency_ms,
        "token_budget": run.token_budget, "status": run.status,
        "token_count": sum(item["token_count"] for item in by_run.get(run.id, []) if item["used"]),
        "items": by_run.get(run.id, []),
        "created_at": run.created_at.isoformat() if run.created_at else None,
    } for run in runs]
