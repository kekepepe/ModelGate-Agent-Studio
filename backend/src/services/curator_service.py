"""Memory Curator and Skill Distiller service.

After Runtime executes and Supervisor approves, this service:
  1. Reads Goal / Tasks / Logs / Handoff / Final Output
  2. Extracts Project Memory, User Memory, Agent Memory
  3. Judges if a Skill can be formed
  4. Generates MemoryDraft and SkillDraft for human review
"""

import hashlib
import json

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord
from src.models.knowledge import MemoryDraft, SkillDraft
from src.models.model import Model
from src.models.supervisor import SupervisorReview
from src.models.workspace import Goal, Task
from src.models.tool import ToolCallRecord
from src.services import memory_vector_service


def generate_memories(db: Session, goal_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate MemoryDrafts from a completed run."""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return {"memory_drafts": [], "skill_drafts": [], "total_memories": 0, "total_skills": 0, "pending_review": 0}

    tasks = db.query(Task).filter(Task.goal_id == goal_id).all()
    logs = db.query(ExecutionLog).filter(ExecutionLog.goal_id == goal_id).all()
    tool_calls = db.query(ToolCallRecord).filter(ToolCallRecord.goal_id == goal_id).all()
    handoffs = db.query(HandoffRecord).filter(HandoffRecord.goal_id == goal_id).all()
    review = db.query(SupervisorReview).filter(SupervisorReview.goal_id == goal_id).order_by(
        SupervisorReview.created_at.desc()).first()

    # Check if drafts already exist for this goal
    existing = db.query(MemoryDraft).filter(MemoryDraft.source_goal_id == goal_id).count()
    if existing > 0:
        return _get_existing_summary(db, goal_id)

    memories = []
    skills = []

    # 1. Project Memory: what we learned about this type of project
    if len(tasks) >= 1:
        completed_tasks = [t for t in tasks if t.status in ("completed", "completed_verified", "completed_unverified")]
        if completed_tasks:
            # V1.5 QL5: LLM-first distillation with the rule template as the
            # honest fallback; provenance recorded either way.
            evidence = {
                "_goal": goal,
                "goal_title": goal.title,
                "goal_status": goal.status,
                "tasks": [{"title": t.title, "status": t.status, "task_type": t.task_type} for t in tasks],
                "tokens_used": sum(t.tokens_used or 0 for t in tasks),
                "error_count": sum(1 for l in logs if l.event_status in ("error", "failed")),
            }
            planner_model = None
            planner_agent = db.query(AgentStation).filter(
                AgentStation.role == "planner", AgentStation.is_enabled == True,  # noqa: E712
            ).first()
            if planner_agent and planner_agent.default_model_id:
                planner_model = db.query(Model).filter(Model.id == planner_agent.default_model_id).first()
            llm_content = _llm_distill(db, evidence, planner_model)
            generated_by = "llm" if llm_content else "rule"
            project_memory = MemoryDraft(
                id=str(uuid.uuid4()),
                source_run_id=run_id,
                source_goal_id=goal_id,
                type="project_memory",
                title=f"Project Pattern: {goal.title}",
                content=llm_content or _build_project_memory_content(goal, tasks, logs),
                confidence=_calc_confidence(tasks, logs),
                reason=f"Auto-generated from completed run ({generated_by})",
                expires_at=datetime.now(timezone.utc) + timedelta(days=90),
            )
            project_memory.set_tags(["project", "pattern", goal.status])
            project_memory.set_metadata(_source_metadata(goal, tasks, logs, tool_calls, run_id))
            db.add(project_memory)
            memories.append(project_memory)

    # 2. Agent Memory: per-agent performance data
    agents_seen = set()
    for t in tasks:
        if t.assigned_agent_id and t.assigned_agent_id not in agents_seen:
            agents_seen.add(t.assigned_agent_id)
            agent = db.query(AgentStation).filter(AgentStation.id == t.assigned_agent_id).first()
            agent_tasks = [t2 for t2 in tasks if t2.assigned_agent_id == t.assigned_agent_id]
            agent_completed = sum(1 for t2 in agent_tasks if t2.status in ("completed", "completed_verified", "completed_unverified"))
            if agent and agent_completed > 0:
                agent_memory = MemoryDraft(
                    id=str(uuid.uuid4()),
                    source_run_id=run_id,
                    source_goal_id=goal_id,
                    type="agent_memory",
                    title=f"{agent.name} Performance: {goal.title}",
                    content=f"Agent {agent.name} ({agent.role}) completed {agent_completed}/{len(agent_tasks)} tasks.\n"
                             f"Total tokens: {sum(t2.tokens_used or 0 for t2 in agent_tasks)}",
                    confidence=agent_completed / max(len(agent_tasks), 1),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=90),
                )
                agent_memory.set_tags([agent.role, "agent_performance"])
                agent_memory.set_metadata(_source_metadata(goal, agent_tasks, logs, tool_calls, run_id))
                db.add(agent_memory)
                memories.append(agent_memory)

    # 3. User Memory: preferences observed (e.g., always uses certain agent combinations)
    if len(tasks) >= 2:
        user_memory = MemoryDraft(
            id=str(uuid.uuid4()),
            source_run_id=run_id,
            source_goal_id=goal_id,
            type="user_memory",
            title=f"User Workflow: {goal.title}",
            content=f"User completed goal with {len(tasks)} tasks across {len(agents_seen)} agents.\n"
                     f"Handoffs: {len(handoffs)}. Errors: {sum(1 for l in logs if l.event_status in ('error','failed'))}.",
            confidence=0.7,
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),
        )
        user_memory.set_tags(["user_preference", "workflow"])
        user_memory.set_metadata(_source_metadata(goal, tasks, logs, tool_calls, run_id))
        db.add(user_memory)
        memories.append(user_memory)

    # 4. Skill Distiller: check if this run can form a reusable skill
    # A reusable Skill must be grounded in at least one evidence-verified
    # task. Planning/research nodes can legitimately finish unverified, so
    # they must not prevent a verified coding path from being distilled.
    terminal_success = {"completed", "completed_verified", "completed_unverified"}
    if len(tasks) >= 2 and all(t.status in terminal_success for t in tasks) and any(
        t.status == "completed_verified" for t in tasks
    ):
        skill = _try_distill_skill(db, goal, tasks, logs, review, run_id)
        if skill:
            db.add(skill)
            skills.append(skill)

    # 5. Experience Memory (V1.2): structured error -> solution pairs so the
    # next run can recall "how we fixed this last time".
    for experience in _extract_experiences(db, goal, tasks, logs, handoffs, tool_calls, run_id):
        db.add(experience)
        memories.append(experience)

    # V1.2: memories and skills enter the RAG pipeline with an embedding
    # produced by the configured adapter (fingerprint stored for lazy re-embed).
    for m in memories:
        memory_vector_service.ensure_memory_embedding(db, m)
    for s in skills:
        memory_vector_service.ensure_skill_embedding(db, s)

    db.commit()
    for m in memories:
        db.refresh(m)
    for s in skills:
        db.refresh(s)

    pending = db.query(MemoryDraft).filter(MemoryDraft.human_approved == None).count()
    pending += db.query(SkillDraft).filter(SkillDraft.human_approved == None).count()

    return {
        "memory_drafts": [m.to_dict() for m in memories],
        "skill_drafts": [s.to_dict() for s in skills],
        "total_memories": len(memories),
        "total_skills": len(skills),
        "pending_review": pending,
    }


def get_evolution_summary(db: Session, goal_id: Optional[str] = None) -> Dict[str, Any]:
    """Get all pending memory and skill drafts, optionally filtered by goal."""
    mem_query = db.query(MemoryDraft)
    skill_query = db.query(SkillDraft)
    if goal_id:
        mem_query = mem_query.filter(MemoryDraft.source_goal_id == goal_id)
        skill_query = skill_query.filter(SkillDraft.source_run_id != None)

    memories = mem_query.order_by(MemoryDraft.created_at.desc()).all()
    skills = skill_query.order_by(SkillDraft.created_at.desc()).all()

    pending = db.query(MemoryDraft).filter(MemoryDraft.human_approved == None).count()
    pending += db.query(SkillDraft).filter(SkillDraft.human_approved == None).count()

    return {
        "memory_drafts": [m.to_dict() for m in memories],
        "skill_drafts": [s.to_dict() for s in skills],
        "total_memories": len(memories),
        "total_skills": len(skills),
        "pending_review": pending,
    }


def approve_memory(db: Session, memory_id: str, approved: bool = True, approved_by: str = "user") -> Dict[str, Any]:
    """Approve or reject a memory draft."""
    mem = db.query(MemoryDraft).filter(MemoryDraft.id == memory_id).first()
    if not mem:
        raise ValueError(f"Memory draft '{memory_id}' not found")
    mem.human_approved = approved
    mem.approved_by = approved_by
    mem.approved_at = datetime.now(timezone.utc)
    # Lazy backfill: rows created before V1.2 (or before approval) get their
    # vector exactly when they become eligible for context selection.
    memory_vector_service.ensure_memory_embedding(db, mem)
    db.commit()
    db.refresh(mem)
    return mem.to_dict()


def approve_skill(db: Session, skill_id: str, approved: bool = True, approved_by: str = "user") -> Dict[str, Any]:
    """Approve or reject a skill draft."""
    skill = db.query(SkillDraft).filter(SkillDraft.id == skill_id).first()
    if not skill:
        raise ValueError(f"Skill draft '{skill_id}' not found")
    skill.human_approved = approved
    skill.approved_by = approved_by
    skill.approved_at = datetime.now(timezone.utc)
    skill.status = "approved" if approved else "rejected"
    memory_vector_service.ensure_skill_embedding(db, skill)
    db.commit()
    db.refresh(skill)
    return skill.to_dict()


def create_user_preference(
    db: Session,
    title: str,
    content: str,
    *,
    created_by: str = "user",
    tags: Optional[List[str]] = None,
) -> MemoryDraft:
    """Persist an explicit user preference (V1.2 D7).

    Preferences are authored by the user, so they are born approved and
    durable (no expiry); context building injects them unconditionally.
    """
    if not title.strip() or not content.strip():
        raise ValueError("Preference title and content are required")
    preference = MemoryDraft(
        id=str(uuid.uuid4()),
        type="user_preference",
        title=title.strip(),
        content=content.strip(),
        confidence=1.0,
        reason=f"Authored explicitly by {created_by}",
        human_approved=True,
        approved_by=created_by,
        approved_at=datetime.now(timezone.utc),
        expires_at=None,
    )
    preference.set_tags(["user_preference", "explicit"] + (tags or []))
    preference.set_metadata({"authored_by": created_by})
    db.add(preference)
    memory_vector_service.ensure_memory_embedding(db, preference)
    db.commit()
    db.refresh(preference)
    return preference.to_dict()


_RESOLUTION_KINDS = {
    "recovered": ("Recovered via", "Task eventually"),
    "replan": ("Resolved via automatic replan",),
    "unresolved": ("Unresolved:",),
}


def _resolution_kind(narrative: str) -> str:
    for kind, prefixes in _RESOLUTION_KINDS.items():
        if narrative.startswith(prefixes):
            return kind
    return "unknown"


def _resolutions_conflict(stored: str, incoming: str) -> bool:
    """Same error class resolving two different ways is a contradiction."""
    stored_kind, incoming_kind = _resolution_kind(stored), _resolution_kind(incoming)
    if stored_kind == "unknown" or incoming_kind == "unknown":
        return False
    return stored_kind != incoming_kind


def resolve_memory_conflict(db: Session, memory_id: str, keep: str = "stored") -> Dict[str, Any]:
    """Human adjudication for a flagged conflict (V1.5 QL6/D4).

    keep='stored' drops the conflicting alternative; keep='incoming' adopts
    it; 'merge' keeps both narratives side by side. Any choice resolves the
    flag — the memory itself is never deleted.
    """
    memory = db.query(MemoryDraft).filter(MemoryDraft.id == memory_id).first()
    if not memory:
        raise ValueError(f"Memory draft '{memory_id}' not found")
    if memory.conflict_state != "conflict":
        raise ValueError(f"Memory '{memory_id}' is not flagged as conflicted")
    metadata = memory.get_metadata()
    conflicting = metadata.pop("conflicting_resolution", None)
    if keep == "incoming" and conflicting:
        metadata["resolution"] = conflicting
        memory.content = f"{memory.content.split(chr(10) + 'Resolution:')[0]}{chr(10)}Resolution: {conflicting}{chr(10)}Occurrences: {metadata.get('occurrence_count', 1)}"
    elif keep == "merge" and conflicting:
        metadata["resolution"] = f"{metadata.get('resolution', '')} | also observed: {conflicting}"
    metadata["adjudicated_at"] = datetime.now(timezone.utc).isoformat()
    memory.set_metadata(metadata)
    memory.conflict_state = "resolved"
    db.commit()
    db.refresh(memory)
    return memory.to_dict()


def record_memory_outcome(db: Session, context_json: Optional[str], task_status: str) -> None:
    """V1.5 QL2: attribute the task outcome to the memories whose context
    actually carried it (the used set), closing the effectiveness loop.

    completed_verified -> +1 success; failed/revision_required/blocked ->
    +1 failure; other terminal states carry no vote.
    """
    if not context_json:
        return
    try:
        context = json.loads(context_json)
    except (json.JSONDecodeError, AttributeError):
        return
    memory_ids = [
        item.get("id")
        for key in ("project_memories", "user_preferences")
        for item in (context.get(key) or [])
        if isinstance(item, dict) and item.get("id")
    ]
    if not memory_ids:
        return
    if task_status == "completed_verified":
        vote = "effectiveness_success"
    elif task_status in {"failed", "revision_required", "blocked"}:
        vote = "effectiveness_failure"
    else:
        return
    memories = db.query(MemoryDraft).filter(MemoryDraft.id.in_(memory_ids)).all()
    for memory in memories:
        setattr(memory, vote, (getattr(memory, vote) or 0) + 1)
    db.flush()


def mark_retrieval_outcomes(db: Session, context_json: Optional[str]) -> None:
    """V1.5 QL2: persist per-item retrieval outcomes for this task's run.

    Items included in the context package (the legacy `used` boolean) become
    outcome='used'; budget-excluded candidates become outcome='ignored'.
    """
    if not context_json:
        return
    try:
        context = json.loads(context_json)
    except (json.JSONDecodeError, AttributeError):
        return
    retrieval_run_id = context.get("retrieval_run_id")
    if not retrieval_run_id:
        return
    from src.models.knowledge import RetrievedContextItem

    db.query(RetrievedContextItem).filter(
        RetrievedContextItem.retrieval_run_id == retrieval_run_id,
    ).update({RetrievedContextItem.outcome: "ignored"}, synchronize_session=False)
    db.query(RetrievedContextItem).filter(
        RetrievedContextItem.retrieval_run_id == retrieval_run_id,
        RetrievedContextItem.used == True,  # noqa: E712 - legacy budget flag
    ).update({RetrievedContextItem.outcome: "used"}, synchronize_session=False)
    db.flush()


def record_skill_outcome(db: Session, context_json: Optional[str], succeeded: bool) -> None:
    """Attribute a verified task result to the approved Skills it actually loaded."""
    if not context_json:
        return
    try:
        context = json.loads(context_json)
        skill_ids = [item.get("id") for item in context.get("skills", []) if item.get("id")]
    except (json.JSONDecodeError, AttributeError):
        return
    if not skill_ids:
        return
    skills = db.query(SkillDraft).filter(SkillDraft.id.in_(skill_ids), SkillDraft.human_approved == True).all()
    for skill in skills:
        if succeeded:
            skill.success_count = (skill.success_count or 0) + 1
        else:
            skill.failure_count = (skill.failure_count or 0) + 1
        skill.last_used_at = datetime.now(timezone.utc)
    db.flush()


LLM_MEMORY_PROMPT = (
    "You are the knowledge curator of a multi-agent execution platform. "
    "Distill the execution evidence below into reusable knowledge. Respond "
    "with ONLY a JSON object — no markdown fences — with exactly these keys: "
    '["title", "content"] where title is <=80 chars and content is <=500 '
    "chars of dense, factual, reusable guidance for future runs. Never invent "
    "work the evidence does not show."
)


def _llm_distill(db: Session, evidence: Dict[str, Any], model: Optional[Any]) -> Optional[str]:
    """V1.5 QL5: ask the run's model to distill memory content.

    Returns None whenever the LLM path is unavailable (mock mode, missing
    model record, provider error, unparseable output) so the caller falls
    back to the rule-based template unchanged.
    """
    if model is None:
        return None
    goal_record = evidence.get("_goal")
    execution_mode = (getattr(goal_record, "execution_mode", None) or settings.execution_mode or "live").lower()
    if execution_mode == "mock":
        return None
    try:
        import asyncio

        from src.services.providers import ModelRequest, get_provider
        from src.services.providers.provider_config import provider_model_name

        provider = get_provider(model=model, execution_mode=execution_mode)
        request = ModelRequest(
            provider=model.provider,
            model=provider_model_name("summarizer", model.model_name),
            messages=[
                {"role": "system", "content": LLM_MEMORY_PROMPT},
                {"role": "user", "content": json.dumps(
                    {k: v for k, v in evidence.items() if not k.startswith("_")},
                    ensure_ascii=False, default=str,
                )},
            ],
            temperature=0.2,
            max_tokens=400,
            metadata={"purpose": "memory_distillation", "model_record_id": model.id},
        )
        response = asyncio.run(provider.generate(request))
        parsed = _extract_json_object(response.content or "")
        content = (parsed or {}).get("content")
        return content if isinstance(content, str) and content.strip() else None
    except Exception:
        return None


def _extract_json_object(text: str) -> Optional[Dict]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start:end + 1])
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


_TERMINAL_SUCCESS = {"completed", "completed_verified", "completed_unverified"}


def _error_signature(message: str) -> str:
    """Stable fingerprint for an error class: lowercase, numbers/ids stripped.

    Keeps "Provider timeout after 3 attempts (req 8f2a...)" and
    "Provider timeout after 5 attempts (req 11bc...)" in the same bucket.
    """
    import re

    normalized = (message or "").lower()
    normalized = re.sub(r"[0-9a-f]{8}-[0-9a-f-]{27,}", " <id> ", normalized)
    normalized = re.sub(r"\b[0-9a-f]{8,}\b", " <hex> ", normalized)
    normalized = re.sub(r"\d+", " <n> ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _resolution_narrative(
    goal: Goal,
    task: Optional[Task],
    tasks: List,
    handoffs: List,
    logs: List,
    agent_names: Optional[Dict[str, str]] = None,
) -> str:
    """How the run recovered (or not) after this error — the 'solution' half."""
    if task is not None:
        for handoff in handoffs:
            if handoff.task_id == task.id:
                names = agent_names or {}
                target = names.get(handoff.to_agent_id, handoff.to_agent_id)
                if handoff.result_after_handoff == "success":
                    return f"Recovered via handoff to {target}; result: success."
                return "Recovered via handoff; the receiving agent resumed the task."
        if task.status in _TERMINAL_SUCCESS:
            return "Task eventually completed after the error (retry within the run)."
    replanned = any(
        getattr(log, "task_id", None) == (task.id if task else None)
        and log.event_type == "runtime.decision"
        and log.event_status == "replan_graph"
        for log in logs
    )
    if replanned:
        return "Resolved via automatic replan: the failed task was replaced."
    return "Unresolved: the run ended without an automatic recovery; replan or manual fix required."


def _extract_experiences(
    db: Session,
    goal: Goal,
    tasks: List,
    logs: List,
    handoffs: List,
    tool_calls: List,
    run_id: Optional[str],
) -> List[MemoryDraft]:
    """Turn error evidence into deduplicated experience memories (V1.2 D5)."""
    task_by_id = {task.id: task for task in tasks}
    agent_names = {a.id: a.name for a in db.query(AgentStation).all()}
    experiences: List[MemoryDraft] = []
    seen_signatures = set()
    for log in logs:
        message = getattr(log, "error_message", None)
        if not message:
            continue
        signature = _error_signature(message)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        task = task_by_id.get(log.task_id) if log.task_id else None
        title = f"Experience: {message[:90].strip()}"
        existing = db.query(MemoryDraft).filter(
            MemoryDraft.type == "experience_memory",
            MemoryDraft.extra_metadata.like(f'%"{signature}"%'),
        ).first()
        narrative = _resolution_narrative(goal, task, tasks, handoffs, logs, agent_names)
        if existing:
            # Mem0-style UPDATE: merge occurrences instead of appending noise.
            metadata = existing.get_metadata()
            metadata["occurrence_count"] = metadata.get("occurrence_count", 1) + 1
            stored_resolution = metadata.get("resolution", "")
            if _resolutions_conflict(stored_resolution, narrative):
                # V1.5 QL6: contradictory resolutions for the same error class
                # — flag for human adjudication, never auto-delete (D4).
                existing.conflict_state = "conflict"
                metadata["conflicting_resolution"] = narrative
            elif narrative.startswith(("Recovered", "Task eventually")):
                metadata["resolution"] = narrative
                existing.content = f"{existing.content.split(chr(10) + 'Resolution:')[0]}{chr(10)}Resolution: {narrative}{chr(10)}Occurrences: {metadata['occurrence_count']}"
            existing.set_metadata(metadata)
            db.flush()
            continue

        agent_name = None
        if task is not None and task.assigned_agent_id:
            agent = db.query(AgentStation).filter(AgentStation.id == task.assigned_agent_id).first()
            agent_name = agent.name if agent else None
        content = (
            f"Error: {message[:300]}\n"
            f"Task: {task.title if task else 'unknown'}\n"
            f"Resolution: {narrative}\n"
            "Occurrences: 1"
        )
        experience = MemoryDraft(
            id=str(uuid.uuid4()),
            source_run_id=run_id,
            source_goal_id=goal.id,
            type="experience_memory",
            title=title,
            content=content,
            confidence=0.6 if narrative.startswith(("Recovered", "Task eventually")) else 0.4,
            reason="Auto-extracted from execution error evidence",
            expires_at=datetime.now(timezone.utc) + timedelta(days=180),
        )
        experience.set_tags(["experience", "error_solution", signature])
        experience.set_metadata({
            "error_signature": signature,
            "resolution": narrative,
            "occurrence_count": 1,
            "agent_name": agent_name,
            "task_type": task.task_type if task else None,
            "source_references": {
                "goal_id": goal.id,
                "run_id": run_id,
                "log_id": log.id,
                "task_id": log.task_id,
            },
        })
        experiences.append(experience)
    return experiences


def _build_project_memory_content(goal: Goal, tasks: List, logs: List) -> str:
    completed = sum(1 for t in tasks if t.status in ("completed", "completed_verified", "completed_unverified"))
    failed = sum(1 for t in tasks if t.status == "failed")
    total_tokens = sum(t.tokens_used or 0 for t in tasks)
    model_ids = {l.model_id for l in logs if l.model_id}
    return (
        f"Goal: {goal.title}\n"
        f"Status: {goal.status}\n"
        f"Tasks: {len(tasks)} (completed: {completed}, failed: {failed})\n"
        f"Total tokens used: {total_tokens}\n"
        f"Models used: {', '.join(model_ids) if model_ids else 'none'}\n"
        f"Log entries: {len(logs)}\n"
    )


def _source_metadata(goal: Goal, tasks: List, logs: List, tool_calls: List, run_id: Optional[str]) -> Dict[str, Any]:
    """Keep candidate knowledge traceable to immutable runtime evidence."""
    return {
        "source_references": {
            "goal_id": goal.id,
            "run_id": run_id,
            "task_ids": [task.id for task in tasks],
            "log_ids": [log.id for log in logs],
            "tool_call_ids": [call.id for call in tool_calls],
        },
    }


def _calc_confidence(tasks: List, logs: List) -> float:
    total = len(tasks)
    if total == 0:
        return 0.5
    completed = sum(1 for t in tasks if t.status in ("completed", "completed_verified", "completed_unverified"))
    error_rate = sum(1 for l in logs if l.event_status in ("error", "failed")) / max(len(logs), 1)
    return round(min(completed / total * (1 - error_rate) + 0.3, 0.95), 2)


def _try_distill_skill(db: Session, goal: Goal, tasks: List, logs: List, review, run_id: Optional[str]) -> Optional[SkillDraft]:
    """Try to distill a reusable skill from this run."""
    verified = [t for t in tasks if t.status == "completed_verified"]
    if not verified:
        return None

    model_ids = list({l.model_id for l in logs if l.model_id})
    agent_ids = list({t.assigned_agent_id for t in tasks if t.assigned_agent_id})
    tool_names = list({l.tool_name for l in logs if l.tool_name})

    skill = SkillDraft(
        id=str(uuid.uuid4()),
        source_run_id=run_id,
        name=f"Skill: {goal.title}",
        scenario=f"When user needs to {goal.title.lower()}",
        input_requirements="Goal description, task breakdown",
        success_criteria=f"{len(verified)} verified task(s); {len(tasks)} task(s) completed",
        output_format=f"Final output: {review.summary[:200] if review and review.summary else 'N/A'}",
        version="1.0",
    )
    skill.set_steps([t.title for t in tasks])
    skill.set_agents(agent_ids)
    skill.set_models(model_ids)
    skill.set_tools(tool_names)
    if logs:
        failures = [f"Error: {l.error_message}" for l in logs if l.error_message][:5]
        skill.set_failures(failures if failures else ["No failures recorded"])
    return skill


def _get_existing_summary(db: Session, goal_id: str) -> Dict[str, Any]:
    memories = db.query(MemoryDraft).filter(MemoryDraft.source_goal_id == goal_id).all()
    skills = db.query(SkillDraft).filter(SkillDraft.source_run_id != None).all()
    pending = db.query(MemoryDraft).filter(MemoryDraft.human_approved == None).count()
    pending += db.query(SkillDraft).filter(SkillDraft.human_approved == None).count()
    return {
        "memory_drafts": [m.to_dict() for m in memories],
        "skill_drafts": [s.to_dict() for s in skills],
        "total_memories": len(memories),
        "total_skills": len(skills),
        "pending_review": pending,
    }


def decay_memories(db: Session) -> Dict[str, int]:
    """V1.5 QL7: confidence decay for memories not retrieved recently.

    Called from the recovery daemon's cycle. Every memory whose metadata
    lacks a last_hit_at newer than 30 days decays confidence by ×0.9
    (floor 0.2); a retrieval hit stamps last_hit_at and resets decay.
    """
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    decayed = 0
    for memory in db.query(MemoryDraft).filter(MemoryDraft.human_approved == True).all():  # noqa: E712
        metadata = memory.get_metadata()
        last_hit = metadata.get("last_hit_at")
        if last_hit:
            try:
                if datetime.fromisoformat(last_hit) > cutoff:
                    continue
            except ValueError:
                pass
        if (memory.confidence or 0) > 0.2:
            memory.confidence = max(0.2, round(memory.confidence * 0.9, 3))
            decayed += 1
    if decayed:
        db.commit()
    return {"decayed": decayed}


def disable_failing_skills(db: Session, *, threshold: int = 3) -> Dict[str, int]:
    """V1.5 QL7: auto-disable skills on >=3 consecutive failures.

    A skill's last N outcomes are inferred from the counters themselves
    (failure_count reaching threshold with success_count unchanged since
    the last disable) — disabled skills await human review, never deleted.
    """
    disabled = 0
    for skill in db.query(SkillDraft).filter(
        SkillDraft.status == "approved",
        SkillDraft.failure_count >= threshold,
    ).all():
        # Only disable when failures dominate the record (rate < 0.25).
        if skill.success_rate < 0.25:
            skill.status = "disabled"
            skill.human_approved = False
            disabled += 1
    if disabled:
        db.commit()
    return {"disabled": disabled}
