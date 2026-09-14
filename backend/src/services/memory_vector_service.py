"""Embedding helpers for MemoryDrafts and SkillDrafts (V1.2).

Keeps memories and skills inside the same embedding pipeline as knowledge
chunks: vectors are produced by the configured adapter (local hash fallback
or any OpenAI-compatible provider), stored as JSON on the row, and guarded
by the adapter fingerprint so a backend switch re-embeds lazily instead of
silently mixing vector spaces.
"""

from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.models.knowledge import MemoryDraft, SkillDraft
from src.services.embedding_service import configured_embedding_adapter
from src.services.retrieval_service import _cosine, _tokens


def embed_text(text: str) -> Tuple[List[float], str]:
    """Embed arbitrary text with the configured adapter."""
    adapter = configured_embedding_adapter()
    return adapter.embed(text), adapter.fingerprint


def memory_embedding_text(memory: MemoryDraft) -> str:
    """The text that represents a memory in vector space."""
    tags = " ".join(memory.get_tags())
    return f"{memory.title}\n{memory.content}\n{tags}".strip()


def skill_embedding_text(skill: SkillDraft) -> str:
    """The text that represents a skill in vector space (Voyager-style index)."""
    steps = " ".join(skill.get_steps())
    failures = " ".join(skill.get_failures())
    return f"{skill.name}\n{skill.scenario or ''}\n{steps}\n{failures}".strip()


def _is_stale(record, fingerprint: str) -> bool:
    return not record.embedding or record.embedding_fingerprint != fingerprint


def ensure_memory_embedding(db: Session, memory: MemoryDraft, *, force: bool = False) -> bool:
    """Embed a memory if missing or produced by a different adapter.

    Returns True when the stored vector changed (caller decides whether to
    commit; curator callers run inside their own transaction).
    """
    vector, fingerprint = embed_text(memory_embedding_text(memory))
    if force or _is_stale(memory, fingerprint):
        memory.set_embedding(vector, fingerprint)
        db.flush()
        return True
    return False


def ensure_skill_embedding(db: Session, skill: SkillDraft, *, force: bool = False) -> bool:
    vector, fingerprint = embed_text(skill_embedding_text(skill))
    if force or _is_stale(skill, fingerprint):
        skill.set_embedding(vector, fingerprint)
        db.flush()
        return True
    return False


def similarity(query_vector: List[float], record) -> float:
    """Cosine similarity between a query vector and a stored record vector.

    Records without a usable vector (or with a different dimensionality)
    score 0.0 so hybrid ranking can still fall back to keyword evidence.
    """
    stored = record.get_embedding() if hasattr(record, "get_embedding") else []
    if not query_vector or not stored or len(stored) != len(query_vector):
        return 0.0
    return max(0.0, _cosine(query_vector, stored))


def _keyword_score(query_tokens: List[str], text: str) -> float:
    """Overlap of distinct query tokens in the record text, normalized."""
    distinct = set(query_tokens)
    if not distinct:
        return 0.0
    text_tokens = set(_tokens(text))
    hits = sum(1 for token in distinct if token in text_tokens)
    return hits / len(distinct)


def _hybrid_search(rows, query, *, limit, require_approved, memory_type=None):
    """Shared hybrid ranking: keyword 0.5 + vector 0.5.

    Rows whose stored vector was produced by a different embedding backend
    contribute keyword evidence only (vector 0.0) instead of mixing spaces.
    """
    query_tokens = _tokens(query)
    query_vector, fingerprint = embed_text(query)
    scored = []
    for row in rows:
        if require_approved is not None and row.human_approved is not require_approved:
            continue
        if memory_type is not None and getattr(row, "type", None) != memory_type:
            continue
        text = memory_embedding_text(row) if isinstance(row, MemoryDraft) else skill_embedding_text(row)
        keyword = _keyword_score(query_tokens, text)
        vector = similarity(query_vector, row) if row.embedding_fingerprint == fingerprint else 0.0
        score = round(keyword * 0.5 + vector * 0.5, 4)
        entry = row.to_dict()
        entry.update({"search_score": score, "keyword_score": round(keyword, 4), "vector_score": round(vector, 4)})
        if isinstance(row, SkillDraft):
            entry["success_rate"] = row.success_rate
        scored.append((score, entry))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for score, entry in scored if score > 0.0][:limit]


def search_memories(
    db: Session,
    query: str,
    *,
    memory_type: Optional[str] = None,
    require_approved: Optional[bool] = None,
    limit: int = 10,
) -> List[Dict]:
    """Hybrid keyword + vector search over memory drafts (V1.2 M3)."""
    rows = db.query(MemoryDraft).order_by(MemoryDraft.created_at.desc()).limit(500).all()
    return _hybrid_search(rows, query, limit=limit, require_approved=require_approved, memory_type=memory_type)


def search_skills(
    db: Session,
    query: str,
    *,
    require_approved: Optional[bool] = None,
    limit: int = 10,
) -> List[Dict]:
    """Hybrid search over skill drafts; success_rate rides along (Voyager-style)."""
    rows = db.query(SkillDraft).order_by(SkillDraft.created_at.desc()).limit(500).all()
    return _hybrid_search(rows, query, limit=limit, require_approved=require_approved)
