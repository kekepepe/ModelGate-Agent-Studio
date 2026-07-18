"""Hybrid retrieval with traceable ranking, citations and context budgets."""

import json
import math
import re
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.models.knowledge import (
    KnowledgeChunk, KnowledgeDocument, KnowledgeSource, RetrievalRun, RetrievedContextItem,
)
from src.services.embedding_service import EmbeddingAdapter, configured_embedding_adapter


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
    adapter = embedding_adapter or configured_embedding_adapter()
    run = RetrievalRun(
        id=str(uuid.uuid4()), goal_id=goal_id, task_id=task_id, agent_id=agent_id,
        query=query, policy=f"hybrid_keyword_embedding_v2:{adapter.name}", token_budget=token_budget,
    )
    filters.update({
        "embedding_model": adapter.model_name,
        "embedding_version": adapter.version,
        "embedding_fingerprint": adapter.fingerprint,
        "embedding_fallback_reason": adapter.fallback_reason,
    })
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
    query_tokens = set(_tokens(query))
    keyword_tokens = sorted(query_tokens, key=len, reverse=True)[:12]
    if keyword_tokens:
        clauses = []
        for token in keyword_tokens:
            pattern = f"%{token}%"
            clauses.extend((
                func.lower(KnowledgeChunk.content).like(pattern),
                func.lower(KnowledgeDocument.path).like(pattern),
                func.lower(KnowledgeDocument.title).like(pattern),
            ))
        keyword_rows = rows.filter(or_(*clauses)).limit(max(100, limit * 20)).all()
    else:
        keyword_rows = []
    # Semantic-only questions still receive a bounded fallback window.  This
    # removes the former unbounded Python scan and repeated JSON decoding while
    # keeping real embedding adapters useful when wording differs.
    candidate_rows = keyword_rows or rows.limit(max(100, limit * 20)).all()
    candidates = []
    query_vector = adapter.embed(query)
    for chunk, document, source in candidate_rows:
        if workspace_scope and source.workspace_scope and not _scope_allows(workspace_scope, source.workspace_scope):
            continue
        content_tokens = set(_tokens(f"{document.path} {document.title} {chunk.symbol_path or ''} {chunk.content}"))
        overlap_count = len(query_tokens & content_tokens)
        keyword = overlap_count / max(1, len(query_tokens))
        stored_vector = json.loads(chunk.embedding or "[]")
        vector = _cosine(query_vector, stored_vector) if len(query_vector) == len(stored_vector) else 0.0
        path_bonus = 0.1 if any(token in document.path.lower() for token in query_tokens) else 0.0
        exact_bonus = 0.15 if query.lower() in chunk.content.lower() else 0.0
        if adapter.name == "local_hash" and overlap_count < 2 and not exact_bonus and not path_bonus:
            # The hash adapter is lexical and its cosine can be positive from
            # collisions; require corroborating terms so unrelated documents
            # do not masquerade as semantic matches.
            continue
        score = keyword * 0.55 + max(0.0, vector) * 0.35 + path_bonus + exact_bonus
        if score >= 0.12:
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
        "candidate_scan_count": len(candidate_rows),
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


STOP_WORDS = {
    "a", "an", "and", "are", "be", "can", "did", "do", "does", "for", "from",
    "how", "in", "is", "of", "on", "the", "to", "uses", "what", "when", "where",
    "which", "with", "user", "client",
}


def _tokens(text: str) -> List[str]:
    return [normalized for item in re.findall(r"[\w.-]+", text.lower())
            if len(item) > 1 and item not in STOP_WORDS
            if (normalized := _normalize_token(item))]


def _normalize_token(token: str) -> str:
    if len(token) > 5 and token.endswith("ied"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ed"):
        return token[:-1]
    if len(token) > 5 and token.endswith("es"):
        return token[:-1]
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _cosine(left: List[float], right: List[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(v * v for v in left)) * math.sqrt(sum(v * v for v in right))
    return sum(a * b for a, b in zip(left, right)) / denominator if denominator else 0.0


def _scope_allows(requested: str, source_scope: str) -> bool:
    requested_value = requested.rstrip("/* ")
    source_value = source_scope.rstrip("/* ")
    return requested_value == source_value or requested_value.startswith(source_value + "/")
