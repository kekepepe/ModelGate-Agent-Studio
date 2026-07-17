"""Build a traceable, bounded context package before every worker run."""
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import or_

from sqlalchemy.orm import Session

from src.models.knowledge import MemoryDraft, SkillDraft
from src.models.workspace import Goal, Task


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
    return {
        "goal": {"id": goal.id, "title": goal.title, "description": goal.description},
        "task": {"id": task.id, "title": task.title, "dependencies": task._get_json("dependencies"), "completion_contract": task._get_json("acceptance_criteria")},
        "project_memories": memory_payload,
        "skills": skill_payload,
        "source_references": source_references,
    }


def _score(query: str, tokens: set, source: str) -> int:
    lowered = source.lower()
    return sum(1 for token in tokens if token in lowered) + (2 if query and query[:24] in lowered else 0)
