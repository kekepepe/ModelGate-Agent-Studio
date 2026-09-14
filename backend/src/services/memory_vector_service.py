"""Embedding helpers for MemoryDrafts and SkillDrafts (V1.2).

Keeps memories and skills inside the same embedding pipeline as knowledge
chunks: vectors are produced by the configured adapter (local hash fallback
or any OpenAI-compatible provider), stored as JSON on the row, and guarded
by the adapter fingerprint so a backend switch re-embeds lazily instead of
silently mixing vector spaces.
"""

from typing import List, Tuple

from sqlalchemy.orm import Session

from src.models.knowledge import MemoryDraft, SkillDraft
from src.services.embedding_service import configured_embedding_adapter
from src.services.retrieval_service import _cosine


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
