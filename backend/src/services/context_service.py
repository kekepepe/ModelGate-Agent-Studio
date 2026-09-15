"""Build a traceable, bounded context package before every worker run.

V1.2: memory and skill selection uses hybrid keyword + vector ranking
(memory_vector_service), approved skills are weighted by their success
rate (Voyager-style), explicit user preferences are injected into every
package unconditionally, replanning pulls similar past experiences, and
planning gets skill suggestions.
"""
import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from sqlalchemy import or_

from sqlalchemy.orm import Session

from src.models.knowledge import ContextPackageSnapshot, KnowledgeSource, MemoryDraft, SkillDraft
from src.models.workspace import Goal, PlanTask, Task, VerificationResult
from src.models.tool import ToolCallRecord
from src.services import memory_vector_service, retrieval_service
from src.services.security_service import redact_data, security_metadata

# V1.2 policy identities (recorded on the package / snapshot for traceability).
HYBRID_POLICY = "hybrid_memory_skill_v1"
# A vector-only match below this floor is treated as embedding noise under
# the lexical hash adapter; keyword evidence alone still matches.
VECTOR_MATCH_FLOOR = 0.35
# Hard cap on unconditionally injected user preferences.
MAX_PREFERENCES = 3


def build_planning_context(db: Session, goal: Goal, limit: int = 3) -> Dict[str, Any]:
    """Return a small, source-backed package for the planning decision."""
    query = f"{goal.title} {goal.description or ''}".lower()
    tokens = {word for word in query.replace("/", " ").split() if len(word) > 2}
    memories = _approved_memories(db)
    query_vector, _ = memory_vector_service.embed_text(query)
    ranked_memories = _hybrid_rank(memories, query, tokens, query_vector)
    selected_memories = [
        item
        for combined, keyword, vector, item in ranked_memories
        if keyword > 0 or vector >= VECTOR_MATCH_FLOOR
    ][:limit]
    skills = _approved_skills(db)
    ranked_skills = _hybrid_rank_skills(skills, query, tokens, query_vector)
    # Planning wants suggestions even without a keyword hit: a high success
    # rate or vector alignment alone can propose a workflow (Voyager-style).
    ranked_skills.sort(key=lambda entry: entry[0], reverse=True)
    selected_skills = [item for _, _, _, item in ranked_skills[:limit]]
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
        "skills": [_skill_suggestion(item) for item in selected_skills],
        "knowledge_items": knowledge["items"],
        "retrieval_run_id": knowledge.get("retrieval_run_id"),
        "citations": [item["citation"] for item in knowledge["items"]],
        "token_count": knowledge.get("token_count", 0),
    }


def build_context_package(db: Session, goal: Goal, task: Task, limit: int = 5) -> Dict[str, Any]:
    query = f"{goal.title} {goal.description or ''} {task.title} {task.description or ''}".lower()
    tokens = {word for word in query.replace("/", " ").split() if len(word) > 2}
    memories = _approved_memories(db)
    query_vector, _ = memory_vector_service.embed_text(query)

    # Explicit user preferences ride along unconditionally (V1.2 D7) and are
    # deliberately excluded from the "matched" signal below.
    preference_memories = [item for item in memories if item.type == "user_preference"][:MAX_PREFERENCES]
    project_memories = [item for item in memories if item.type != "user_preference"]

    ranked_memories = _hybrid_rank(project_memories, query, tokens, query_vector)
    selected_memories = [
        item for combined, keyword, vector, item in ranked_memories
        if keyword > 0 or vector >= VECTOR_MATCH_FLOOR
    ][:limit]

    skills = _approved_skills(db)
    ranked_skills = _hybrid_rank_skills(skills, query, tokens, query_vector)
    selected_skills = [
        item for combined, keyword, vector, item in ranked_skills
        if keyword > 0 or vector >= VECTOR_MATCH_FLOOR
    ][:limit]

    memory_payload = [
        {"id": item.id, "title": item.title, "content": item.content, "source_goal_id": item.source_goal_id,
         "confidence": item.confidence, "source_references": item.get_metadata().get("source_references", {})}
        for item in selected_memories
    ]
    skill_payload = [_skill_suggestion(item, include_source=True) for item in selected_skills]
    preference_payload = [
        {"id": item.id, "title": item.title, "content": item.content}
        for item in preference_memories
    ]
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
    matched = bool(memory_payload or skill_payload or knowledge["items"])
    payload = {
        "goal": {"id": goal.id, "title": goal.title, "description": goal.description},
        "task": {"id": task.id, "title": task.title, "dependencies": task._get_json("dependencies"), "completion_contract": task._get_json("acceptance_criteria")},
        "retrieval_reason": _retrieval_reason(task, matched, should_retrieve),
        "query": query,
        "policy": f"{HYBRID_POLICY}:{knowledge.get('policy') or 'no_knowledge_sources'}",
        "project_memories": memory_payload,
        "user_preferences": preference_payload,
        "skills": skill_payload,
        "knowledge_items": knowledge["items"],
        "retrieval_run_id": knowledge.get("retrieval_run_id"),
        "citations": [item["citation"] for item in knowledge["items"]],
        "source_references": source_references,
    }
    payload["token_count"] = _estimate_tokens(payload)
    return payload


def _approved_memories(db: Session) -> List[MemoryDraft]:
    return db.query(MemoryDraft).filter(
        MemoryDraft.human_approved == True,
        or_(MemoryDraft.expires_at == None, MemoryDraft.expires_at > datetime.now(timezone.utc)),
    ).order_by(MemoryDraft.confidence.desc()).all()


def _approved_skills(db: Session) -> List[SkillDraft]:
    return db.query(SkillDraft).filter(
        SkillDraft.human_approved == True,
        SkillDraft.status == "approved",
    ).all()


def _hybrid_rank(
    memories: List[MemoryDraft], query: str, tokens: set, query_vector: List[float],
) -> List[Tuple[float, float, float, MemoryDraft]]:
    """Keyword + vector hybrid ranking (V1.2 D3).

    Keyword evidence alone still ranks (it powers hash-embedding rows and
    stale fingerprints); vectors add alignment when the stored fingerprint
    matches the configured adapter (memory_vector_service returns 0.0
    otherwise, so vector spaces never mix).
    """
    scored: List[Tuple[float, float, float, MemoryDraft]] = []
    for item in memories:
        text = f"{item.title} {item.content} {' '.join(item.get_tags())}"
        keyword = min(1.0, _score(query, tokens, text) / 3)
        vector = memory_vector_service.similarity(query_vector, item)
        scored.append((keyword * 0.5 + vector * 0.5, keyword, vector, item))
    scored.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
    return scored


def _hybrid_rank_skills(
    skills: List[SkillDraft], query: str, tokens: set, query_vector: List[float],
) -> List[Tuple[float, float, float, SkillDraft]]:
    """Hybrid ranking with a success-rate weight (V1.2 D4, Voyager-style).

    weight = 0.8 + 0.4 * success_rate keeps an unproven skill neutral (0.5
    success rate -> weight 1.0) while a proven one gains up to +20% and a
    failing one loses up to -20%.
    """
    scored: List[Tuple[float, float, float, SkillDraft]] = []
    for item in skills:
        text = f"{item.name} {item.scenario or ''} {item.success_criteria or ''} {' '.join(item.get_steps())}"
        keyword = min(1.0, _score(query, tokens, text) / 3)
        vector = memory_vector_service.similarity(query_vector, item)
        weight = 0.8 + 0.4 * item.success_rate
        scored.append(((keyword * 0.5 + vector * 0.5) * weight, keyword, vector, item))
    scored.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
    return scored


def _skill_suggestion(item: SkillDraft, *, include_source: bool = False) -> Dict[str, Any]:
    """Progressive disclosure (V1.2 D6): summary + a few steps in context;
    the full record stays behind GET /knowledge/skills/{id}."""
    steps = item.get_steps()
    payload: Dict[str, Any] = {
        "id": item.id,
        "name": item.name,
        "scenario": item.scenario,
        "success_rate": item.success_rate,
        "success_count": item.success_count,
        "failure_count": item.failure_count,
        "steps": steps[:3],
        "steps_total": len(steps),
    }
    if include_source:
        payload["source_run_id"] = item.source_run_id
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
    payload = redact_data(payload)
    payload.setdefault("security", security_metadata())
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
    skills = _approved_skills(db)
    query_vector, _ = memory_vector_service.embed_text(query)
    ranked_skills = _hybrid_rank_skills(skills, query.lower(), query_tokens, query_vector)
    matched_skills = [
        item
        for combined, keyword, vector, item in ranked_skills
        if keyword > 0 or vector >= VECTOR_MATCH_FLOOR
    ][:5]
    # V1.2: pull similar past experiences ("how we fixed this last time")
    # so the replan decision inherits prior error resolutions.
    experiences = memory_vector_service.search_memories(
        db, query, memory_type="experience_memory", require_approved=True, limit=3,
    )
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
        "experiences": [
            {"id": item["id"], "title": item["title"], "content": item["content"],
             "error_signature": item["metadata"].get("error_signature"),
             "occurrence_count": item["metadata"].get("occurrence_count", 1)}
            for item in experiences
        ],
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
