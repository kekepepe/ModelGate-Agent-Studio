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
            project_memory = MemoryDraft(
                id=str(uuid.uuid4()),
                source_run_id=run_id,
                source_goal_id=goal_id,
                type="project_memory",
                title=f"Project Pattern: {goal.title}",
                content=_build_project_memory_content(goal, tasks, logs),
                confidence=_calc_confidence(tasks, logs),
                reason="Auto-generated from completed run",
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
            if narrative.startswith(("Recovered", "Task eventually")):
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
