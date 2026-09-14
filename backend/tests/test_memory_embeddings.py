"""V1.2 M1: memories and skills carry embeddings inside the RAG pipeline.

The curator embeds every generated draft, approval lazily backfills older
rows, and a stored fingerprint mismatch (embedding backend switched) forces
a re-embed instead of silently mixing vector spaces.
"""
import uuid

from src.models.knowledge import MemoryDraft
from src.models.workspace import Goal, Task
from src.services import memory_vector_service
from src.services.curator_service import approve_memory, generate_memories
from src.services.embedding_service import configured_embedding_adapter


def _completed_goal(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Migrate billing service", status="completed")
    plan = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Plan billing migration", status="completed_unverified")
    code = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Migrate billing tables", status="completed_verified")
    db_session.add_all([goal, plan, code])
    db_session.commit()
    return goal


def test_generated_memories_and_skills_carry_embeddings(db_session):
    goal = _completed_goal(db_session)

    generate_memories(db_session, goal.id, run_id="run-embed-1")

    adapter = configured_embedding_adapter()
    memories = db_session.query(MemoryDraft).all()
    assert memories, "curator should produce memory drafts"
    for memory in memories:
        vector = memory.get_embedding()
        assert vector, f"memory {memory.type} missing embedding"
        assert memory.embedding_fingerprint == adapter.fingerprint
        assert len(vector) == (adapter.dimensions or 64)


def test_ensure_embedding_is_idempotent_until_fingerprint_changes(db_session):
    memory = MemoryDraft(
        id=str(uuid.uuid4()), type="project_memory",
        title="Prefers pytest", content="User prefers pytest over unittest.",
    )
    memory.set_tags(["testing"])
    db_session.add(memory)
    db_session.commit()

    assert memory_vector_service.ensure_memory_embedding(db_session, memory) is True
    first_vector = memory.get_embedding()
    assert memory_vector_service.ensure_memory_embedding(db_session, memory) is False
    assert memory.get_embedding() == first_vector

    # Simulate an embedding backend switch: the stored fingerprint no longer
    # matches the configured adapter, so the vector must be rebuilt.
    memory.embedding_fingerprint = "openai_compatible:text-embedding-3-small:1"
    assert memory_vector_service.ensure_memory_embedding(db_session, memory) is True
    assert memory.embedding_fingerprint == configured_embedding_adapter().fingerprint


def test_approve_memory_lazily_backfills_embedding(db_session):
    memory = MemoryDraft(
        id=str(uuid.uuid4()), type="project_memory",
        title="Legacy row", content="Created before the V1.2 embedding columns.",
    )
    db_session.add(memory)
    db_session.commit()
    assert memory.get_embedding() == []

    approve_memory(db_session, memory.id, approved=True, approved_by="tester")

    db_session.refresh(memory)
    assert memory.get_embedding() != []
    assert memory.embedding_fingerprint == configured_embedding_adapter().fingerprint


def test_similarity_handles_missing_and_mismatched_vectors(db_session):
    memory = MemoryDraft(
        id=str(uuid.uuid4()), type="project_memory",
        title="Query target", content="Deploys happen on Fridays only.",
    )
    db_session.add(memory)
    db_session.commit()
    memory_vector_service.ensure_memory_embedding(db_session, memory)

    query_vector, _ = memory_vector_service.embed_text("When do deploys happen?")

    # Same-text-derived vectors align positively (the 64-dim hash adapter is
    # lexical, so ~0.4 is a strong match for it; mismatched/empty must be 0).
    assert memory_vector_service.similarity(query_vector, memory) > 0.2

    class _Mismatched:
        def get_embedding(self):
            return [0.0] * (len(query_vector) + 8)

    assert memory_vector_service.similarity(query_vector, _Mismatched()) == 0.0

    class _Empty:
        def get_embedding(self):
            return []

    assert memory_vector_service.similarity(query_vector, _Empty()) == 0.0
