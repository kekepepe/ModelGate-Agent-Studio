"""Build a traceable, bounded context package before every worker run."""
import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import or_

from sqlalchemy.orm import Session

from src.models.knowledge import ContextPackageSnapshot, KnowledgeSource, MemoryDraft, SkillDraft
from src.models.workspace import Goal, PlanTask, Task, VerificationResult
from src.models.tool import ToolCallRecord
from src.services import retrieval_service


def build_planning_context(db: Session, goal: Goal, limit: int = 3) -> Dict[str, Any]:
    """Return a small, source-backed package for the planning decision.

    This intentionally reuses the current reviewed Memory/Skill store. P1 will
    replace the lightweight ranking with the shared retrieval pipeline.
    """
    query = f"{goal.title} {goal.description or ''}".lower()
    tokens = {word for word in query.replace("/", " ").split() if len(word) > 2}
    memories = db.query(MemoryDraft).filter(
        MemoryDraft.human_approved == True,
        or_(MemoryDraft.expires_at == None, MemoryDraft.expires_at > datetime.now(timezone.utc)),
    ).order_by(MemoryDraft.confidence.desc()).all()
    ranked_memories = sorted(
        memories,
        key=lambda item: _score(query, tokens, f"{item.title} {item.content} {' '.join(item.get_tags())}"),
        reverse=True,
    )
    selected_memories = [
        item for item in ranked_memories
        if _score(query, tokens, f"{item.title} {item.content}") > 0
    ][:limit]
    skills = db.query(SkillDraft).filter(
        SkillDraft.human_approved == True,
        SkillDraft.status == "approved",
    ).all()
    selected_skills = [
        item for item in skills
        if _score(query, tokens, f"{item.name} {item.scenario or ''} {item.success_criteria or ''}") > 0
    ][:limit]
    knowledge = _retrieve_knowledge(
        db, query=query, goal=goal, task=None, token_budget=600,
        workspace_scope=None, enabled=_has_active_sources(db),
    )
    return {
        "workspace_root": goal.workspace_root,
        "memories": [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "source_goal_id": item.source_goal_id,
            }
            for item in selected_memories
        ],
        "skills": [
            {
                "id": item.id,
                "name": item.name,
                "steps": item.get_steps(),
                "source_run_id": item.source_run_id,
            }
            for item in selected_skills
        ],
        "knowledge_items": knowledge["items"],
        "retrieval_run_id": knowledge.get("retrieval_run_id"),
        "citations": [item["citation"] for item in knowledge["items"]],
        "token_count": knowledge.get("token_count", 0),
    }


def build_context_package(db: Session, goal: Goal, task: Task, limit: int = 5) -> Dict[str, Any]:
    query = f"{goal.title} {goal.description or ''} {task.title} {task.description or ''}".lower()
    tokens = {word for word in query.replace("/", " ").split() if len(word) > 2}
    memories = db.query(MemoryDraft).filter(
        MemoryDraft.human_approved == True,
        or_(MemoryDraft.expires_at == None, MemoryDraft.expires_at > datetime.now(timezone.utc)),
    ).order_by(MemoryDraft.confidence.desc()).all()
    ranked_memories = sorted(memories, key=lambda item: _score(query, tokens, f"{item.title} {item.content} {' '.join(item.get_tags())}"), reverse=True)
    selected_memories = [item for item in ranked_memories if _score(query, tokens, f"{item.title} {item.content}") > 0][:limit]
    skills = db.query(SkillDraft).filter(SkillDraft.human_approved == True, SkillDraft.status == "approved").all()
    selected_skills = [item for item in skills if _score(query, tokens, f"{item.name} {item.scenario or ''} {item.success_criteria or ''}") > 0][:limit]
    memory_payload = [{"id": item.id, "title": item.title, "content": item.content, "source_goal_id": item.source_goal_id, "confidence": item.confidence, "source_references": item.get_metadata().get("source_references", {})} for item in selected_memories]
    skill_payload = [{"id": item.id, "name": item.name, "steps": item.get_steps(), "source_run_id": item.source_run_id} for item in selected_skills]
    source_references = [
        {"memory_id": item["id"], **item["source_references"]}
        for item in memory_payload if item["source_references"]
    ] + [
        {"skill_id": item["id"], "run_id": item["source_run_id"]}
        for item in skill_payload if item["source_run_id"]
    ]
    plan_task = db.query(PlanTask).filter(PlanTask.id == task.plan_task_id).first() if task.plan_task_id else None
    should_retrieve = _should_retrieve_knowledge(task) and _has_active_sources(db)
    knowledge = _retrieve_knowledge(
        db, query=query, goal=goal, task=task, token_budget=1200,
        workspace_scope=plan_task.workspace_scope if plan_task else None,
        enabled=should_retrieve,
    )
    source_references.extend([
        {"source_id": item["source_id"], "chunk_id": item["chunk_id"], "citation": item["citation"]}
        for item in knowledge["items"]
    ])
    payload = {
        "goal": {"id": goal.id, "title": goal.title, "description": goal.description},
        "task": {"id": task.id, "title": task.title, "dependencies": task._get_json("dependencies"), "completion_contract": task._get_json("acceptance_criteria")},
        "retrieval_reason": _retrieval_reason(task, bool(memory_payload or skill_payload or knowledge["items"]), should_retrieve),
        "query": query,
        "policy": knowledge.get("policy") or "approved_memory_skill_keyword_v0",
        "project_memories": memory_payload,
        "skills": skill_payload,
        "knowledge_items": knowledge["items"],
        "retrieval_run_id": knowledge.get("retrieval_run_id"),
        "citations": [item["citation"] for item in knowledge["items"]],
        "source_references": source_references,
    }
    payload["token_count"] = _estimate_tokens(payload)
    return payload


def _score(query: str, tokens: set, source: str) -> int:
    lowered = source.lower()
    return sum(1 for token in tokens if token in lowered) + (2 if query and query[:24] in lowered else 0)


def _retrieval_reason(task: Task, matched: bool, knowledge_enabled: bool = False) -> str:
    capabilities = task._get_json("required_capabilities")
    if matched:
        return "Approved project knowledge, Memory or Skill matched the Goal and Task query."
    if not knowledge_enabled:
        return "Knowledge RAG was gated off because this Task did not require it or no active source exists."
    if capabilities:
        return "Task capability context was evaluated, but no approved relevant knowledge matched."
    return "No project knowledge was required or matched; only Goal and Task facts were included."


def _estimate_tokens(payload: Dict[str, Any]) -> int:
    # Stable provider-independent estimate for budgeting before tokenizer-specific P1 adapters.
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return max(1, (len(serialized) + 3) // 4)


def persist_context_snapshot(db: Session, worker_id: str, plan_version_id: str, payload: Dict[str, Any]) -> ContextPackageSnapshot:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    snapshot = ContextPackageSnapshot(
        id=str(uuid.uuid4()), worker_id=worker_id, plan_version_id=plan_version_id,
        retrieval_run_id=payload.get("retrieval_run_id"), payload=serialized,
        token_count=int(payload.get("token_count", 0)),
        checksum=hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
    )
    db.add(snapshot)
    db.flush()
    return snapshot


def build_replan_context(db: Session, goal: Goal, tasks: List[Task], reason: str) -> Dict[str, Any]:
    """Retrieve repair knowledge and exact immutable Runtime evidence."""
    task_ids = [task.id for task in tasks]
    query = " ".join([goal.title, goal.description or "", reason, *[task.title for task in tasks]])
    knowledge = _retrieve_knowledge(
        db, query=query.lower(), goal=goal, task=tasks[0] if tasks else None,
        token_budget=800, workspace_scope=None, enabled=_has_active_sources(db),
    )
    query_tokens = {word for word in query.lower().split() if len(word) > 2}
    skills = db.query(SkillDraft).filter(
        SkillDraft.human_approved == True, SkillDraft.status == "approved",
    ).all()
    matched_skills = [
        skill for skill in skills
        if _score(query.lower(), query_tokens, f"{skill.name} {skill.scenario or ''} {skill.success_criteria or ''}") > 0
    ][:5]
    verifications = (
        db.query(VerificationResult)
        .filter(VerificationResult.task_id.in_(task_ids))
        .order_by(VerificationResult.created_at.desc())
        .limit(20).all()
        if task_ids else []
    )
    tool_failures = (
        db.query(ToolCallRecord)
        .filter(ToolCallRecord.task_id.in_(task_ids), ToolCallRecord.status != "completed")
        .order_by(ToolCallRecord.created_at.desc())
        .limit(10).all()
        if task_ids else []
    )
    return {
        "retrieval_run_id": knowledge.get("retrieval_run_id"),
        "knowledge_items": knowledge["items"],
        "citations": [item["citation"] for item in knowledge["items"]],
        "skills": [{"id": skill.id, "name": skill.name, "steps": skill.get_steps()} for skill in matched_skills],
        "verification_evidence": [
            {"task_id": item.task_id, "criterion": item.criterion_type, "status": item.status,
             "evidence": item.evidence, "exit_code": item.exit_code}
            for item in verifications
        ],
        "tool_failures": [
            {"task_id": item.task_id, "tool": item.tool_name, "status": item.status,
             "error": item.error_message}
            for item in tool_failures
        ],
        "token_count": knowledge.get("token_count", 0),
    }


def _has_active_sources(db: Session) -> bool:
    return db.query(KnowledgeSource.id).filter(KnowledgeSource.status == "active").first() is not None


def _should_retrieve_knowledge(task: Task) -> bool:
    capabilities = set(task._get_json("required_capabilities"))
    return task.task_type in {"planning", "research", "coding", "verification", "merge"} or bool(
        capabilities.intersection({"research", "code_read", "code_edit", "review", "security_review", "document_write"})
    )


def _retrieve_knowledge(db: Session, *, query: str, goal: Goal, task: Task, token_budget: int,
                        workspace_scope: str, enabled: bool) -> Dict[str, Any]:
    if not enabled:
        return {"items": [], "token_count": 0}
    return retrieval_service.retrieve(
        db, query=query, goal_id=goal.id, task_id=task.id if task else None,
        agent_id=task.assigned_agent_id if task else None,
        token_budget=token_budget, workspace_scope=workspace_scope,
    )
