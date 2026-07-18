import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from src.models.knowledge import (
    ContextPackageSnapshot,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeSource,
    RetrievalRun,
    RetrievedContextItem,
)


def test_p1_knowledge_traceability_graph_persists(db_session):
    source = KnowledgeSource(name="Architecture", type="workspace", uri="docs", workspace_scope="docs/**")
    db_session.add(source)
    db_session.flush()
    document = KnowledgeDocument(source_id=source.id, path="docs/architecture.md", title="Architecture", checksum="doc-sha")
    db_session.add(document)
    db_session.flush()
    chunks = [
        KnowledgeChunk(document_id=document.id, content="System boundary", chunk_index=0, token_count=4),
        KnowledgeChunk(document_id=document.id, content="Runtime contract", chunk_index=1, token_count=4),
    ]
    run = RetrievalRun(goal_id="goal", task_id="task", agent_id="agent", query="runtime boundary", policy="hybrid_v1", token_budget=200)
    db_session.add_all([*chunks, run])
    db_session.flush()
    item = RetrievedContextItem(
        retrieval_run_id=run.id, source_type="knowledge_chunk", source_id=source.id,
        chunk_id=chunks[0].id, score=0.9, rank=1, used=True,
        citation="docs/architecture.md#chunk-0", token_count=4,
    )
    snapshot = ContextPackageSnapshot(
        worker_id="worker", plan_version_id="plan", retrieval_run_id=run.id,
        payload="{}", token_count=4, checksum="snapshot-sha",
    )
    db_session.add_all([item, snapshot])
    db_session.commit()

    assert db_session.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.id).count() == 2
    assert db_session.query(RetrievedContextItem).filter(RetrievedContextItem.retrieval_run_id == run.id).one().used is True
    assert db_session.query(ContextPackageSnapshot).filter(ContextPackageSnapshot.worker_id == "worker").one().checksum == "snapshot-sha"


def test_document_path_and_chunk_index_are_idempotency_keys(db_session):
    source_id = str(uuid.uuid4())
    first = KnowledgeDocument(source_id=source_id, path="README.md", title="Readme", checksum="a")
    duplicate = KnowledgeDocument(source_id=source_id, path="README.md", title="Readme 2", checksum="b")
    db_session.add_all([first, duplicate])
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    document = KnowledgeDocument(source_id=source_id, path="README.md", title="Readme", checksum="a")
    db_session.add(document)
    db_session.flush()
    db_session.add_all([
        KnowledgeChunk(document_id=document.id, content="one", chunk_index=0),
        KnowledgeChunk(document_id=document.id, content="two", chunk_index=0),
    ])
    with pytest.raises(IntegrityError):
        db_session.commit()
