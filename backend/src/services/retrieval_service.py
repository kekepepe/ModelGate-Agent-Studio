"""Hybrid retrieval with traceable ranking, citations and context budgets."""

import json
import math
import re
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol

from sqlalchemy.orm import Session

from src.models.knowledge import (
    KnowledgeChunk, KnowledgeDocument, KnowledgeSource, RetrievalRun, RetrievedContextItem,
)
from src.services.knowledge_source_service import _hash_embedding


class EmbeddingAdapter(Protocol):
    def embed(self, text: str) -> List[float]: ...


class LocalHashEmbeddingAdapter:
    """Offline deterministic adapter; replaceable without changing retrieval records."""
    def embed(self, text: str) -> List[float]:
        return _hash_embedding(text)


@dataclass
class Candidate:
    chunk: KnowledgeChunk
    document: KnowledgeDocument
    source: KnowledgeSource
    keyword_score: float
    vector_score: float
    score: float


def retrieve(
    db: Session,
    *,
    query: str,
    goal_id: str = None,
    task_id: str = None,
    agent_id: str = None,
    token_budget: int = 1200,
    source_ids: Optional[List[str]] = None,
    workspace_scope: str = None,
    limit: int = 20,
    embedding_adapter: EmbeddingAdapter = None,
) -> Dict:
    if not query.strip():
        raise ValueError("Retrieval query cannot be empty")
    if token_budget < 0:
        raise ValueError("token_budget cannot be negative")
    started = time.time()
    filters = {"source_ids": source_ids or [], "workspace_scope": workspace_scope}
    run = RetrievalRun(
        id=str(uuid.uuid4()), goal_id=goal_id, task_id=task_id, agent_id=agent_id,
        query=query, policy="hybrid_keyword_hash_embedding_v1", token_budget=token_budget,
    )
    run.set_filters(filters)
    db.add(run); db.flush()

    rows = db.query(KnowledgeChunk, KnowledgeDocument, KnowledgeSource).join(
        KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id,
    ).join(
        KnowledgeSource, KnowledgeSource.id == KnowledgeDocument.source_id,
    ).filter(
        KnowledgeChunk.status == "active",
        KnowledgeDocument.status == "indexed",
        KnowledgeSource.status == "active",
    )
    if source_ids:
        rows = rows.filter(KnowledgeSource.id.in_(source_ids))
    candidates = []
    query_tokens = set(_tokens(query))
    query_vector = (embedding_adapter or LocalHashEmbeddingAdapter()).embed(query)
    for chunk, document, source in rows.all():
        if workspace_scope and source.workspace_scope and not _scope_allows(workspace_scope, source.workspace_scope):
            continue
        content_tokens = set(_tokens(f"{document.path} {document.title} {chunk.symbol_path or ''} {chunk.content}"))
        keyword = len(query_tokens & content_tokens) / max(1, len(query_tokens))
        vector = _cosine(query_vector, json.loads(chunk.embedding or "[]"))
        path_bonus = 0.1 if any(token in document.path.lower() for token in query_tokens) else 0.0
        exact_bonus = 0.15 if query.lower() in chunk.content.lower() else 0.0
        score = keyword * 0.55 + max(0.0, vector) * 0.35 + path_bonus + exact_bonus
        if score > 0:
            candidates.append(Candidate(chunk, document, source, keyword, vector, score))
    candidates.sort(key=lambda item: (-item.score, item.document.path, item.chunk.chunk_index))
    candidates = candidates[:limit]

    remaining, selected = token_budget, []
    records = []
    for rank, candidate in enumerate(candidates, start=1):
        used = candidate.chunk.token_count <= remaining and candidate.chunk.token_count > 0
        if used:
            remaining -= candidate.chunk.token_count
            selected.append(candidate)
        citation = f"{candidate.document.path}#chunk-{candidate.chunk.chunk_index}"
        records.append(RetrievedContextItem(
            id=str(uuid.uuid4()), retrieval_run_id=run.id,
            source_type="knowledge_chunk", source_id=candidate.source.id,
            chunk_id=candidate.chunk.id, score=candidate.score, rank=rank, used=used,
            citation=citation, token_count=candidate.chunk.token_count,
        ))
    db.add_all(records)
    run.latency_ms = int((time.time() - started) * 1000)
    run.status = "empty" if not candidates else "completed"
    db.commit()
    return {
        "retrieval_run_id": run.id,
        "query": query,
        "policy": run.policy,
        "token_budget": token_budget,
        "token_count": token_budget - remaining,
        "items": [
            {"rank": rank, "source_id": item.source.id, "document_id": item.document.id,
             "chunk_id": item.chunk.id, "path": item.document.path,
             "content": item.chunk.content, "score": round(item.score, 6),
             "citation": f"{item.document.path}#chunk-{item.chunk.chunk_index}",
             "token_count": item.chunk.token_count}
            for rank, item in enumerate(selected, start=1)
        ],
        "candidate_count": len(candidates),
        "latency_ms": run.latency_ms,
    }


def get_runs(db: Session, goal_id: str) -> List[Dict]:
    runs = db.query(RetrievalRun).filter(RetrievalRun.goal_id == goal_id).order_by(RetrievalRun.created_at.desc()).all()
    return [{"id": run.id, "goal_id": run.goal_id, "task_id": run.task_id,
             "agent_id": run.agent_id, "query": run.query, "policy": run.policy,
             "filters": run.get_filters(), "latency_ms": run.latency_ms,
             "token_budget": run.token_budget, "status": run.status,
             "created_at": run.created_at.isoformat() if run.created_at else None}
            for run in runs]


def _tokens(text: str) -> List[str]:
    return [item for item in re.findall(r"[\w.-]+", text.lower()) if len(item) > 1]


def _cosine(left: List[float], right: List[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(v * v for v in left)) * math.sqrt(sum(v * v for v in right))
    return sum(a * b for a, b in zip(left, right)) / denominator if denominator else 0.0


def _scope_allows(requested: str, source_scope: str) -> bool:
    requested_value = requested.rstrip("/* ")
    source_value = source_scope.rstrip("/* ")
    return requested_value == source_value or requested_value.startswith(source_value + "/") or source_value.startswith(requested_value + "/")
