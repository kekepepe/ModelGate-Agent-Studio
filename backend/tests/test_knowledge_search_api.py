"""V1.2 M3: preference / search / skill-detail API + unified /context/retrieve."""
import uuid

from src.models.knowledge import MemoryDraft, SkillDraft
from src.services import memory_vector_service


def _seed_memory(db_session, *, title, content, mtype="project_memory", approved=True):
    memory = MemoryDraft(
        id=str(uuid.uuid4()), type=mtype, title=title, content=content,
        human_approved=approved,
    )
    db_session.add(memory)
    db_session.commit()
    memory_vector_service.ensure_memory_embedding(db_session, memory)
    return memory


def test_search_memories_ranks_relevant_first(db_session):
    _seed_memory(db_session, title="Deploy windows", content="Deploys happen on Fridays only, never Mondays.")
    _seed_memory(db_session, title="Coffee budget", content="The team prefers oat milk in the espresso machine.")

    results = memory_vector_service.search_memories(
        db_session, "When are deploys allowed?", require_approved=True, limit=5,
    )

    assert results, "expected at least one hit"
    assert "Deploy windows" in results[0]["title"]
    assert results[0]["search_score"] > 0.0
    assert all("search_score" in item and "keyword_score" in item for item in results)


def test_search_memories_keyword_only_still_works_for_stale_vectors(db_session):
    memory = _seed_memory(db_session, title="Release checklist", content="Always run the migration dry-run before shipping.")
    memory.embedding_fingerprint = "openai_compatible:some-other-model:1"  # backend switched
    db_session.commit()

    results = memory_vector_service.search_memories(db_session, "migration dry-run before shipping")

    assert results
    assert results[0]["title"] == "Release checklist"
    assert results[0]["vector_score"] == 0.0, "stale vectors must not pollute the vector space"
    assert results[0]["keyword_score"] > 0.0


def test_preference_api_creates_approved_preference(client, db_session):
    resp = client.post("/api/v1/knowledge/preferences", json={
        "title": "Always pytest",
        "content": "User prefers pytest with fixtures over unittest classes.",
        "created_by": "mavis",
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["type"] == "user_preference"
    assert data["human_approved"] is True
    assert data["metadata"]["authored_by"] == "mavis"


def test_preference_api_rejects_blank_title(client):
    resp = client.post("/api/v1/knowledge/preferences", json={"title": "  ", "content": "x"})
    assert resp.status_code == 400


def test_memories_search_endpoint_filters_by_type(client, db_session):
    _seed_memory(db_session, title="Experience: parser timeout", content="Provider timeout on parser task.", mtype="experience_memory")
    _seed_memory(db_session, title="Deploy windows", content="Deploys happen on Fridays only.")

    resp = client.get("/api/v1/knowledge/memories/search", params={"q": "provider timeout parser", "type": "experience_memory"})
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert items
    assert all(item["type"] == "experience_memory" for item in items)


def test_skill_detail_endpoint_exposes_success_rate(client, db_session):
    skill = SkillDraft(id=str(uuid.uuid4()), name="Fix flaky tests", scenario="When the suite flakes", status="approved", human_approved=True)
    skill.success_count = 3
    skill.failure_count = 1
    db_session.add(skill)
    db_session.commit()

    resp = client.get(f"/api/v1/knowledge/skills/{skill.id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["success_rate"] == 0.75

    missing = client.get("/api/v1/knowledge/skills/does-not-exist")
    assert missing.status_code == 404


def test_unified_retrieve_includes_memories_and_skills(client, db_session):
    _seed_memory(db_session, title="Deploy windows", content="Deploys happen on Fridays only.")
    skill = SkillDraft(id=str(uuid.uuid4()), name="Deploy checklist", scenario="Deploy Fridays", status="approved", human_approved=True)
    skill.set_steps(["freeze", "tag", "ship"])
    db_session.add(skill)
    db_session.commit()
    memory_vector_service.ensure_skill_embedding(db_session, skill)

    resp = client.post("/api/v1/context/retrieve", json={
        "query": "deploy on Fridays",
        "source_types": ["memory", "skill"],
        "limit": 5,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["policy"] == "unified_memory_skill_knowledge_v1"
    assert data["memories"] and data["memories"][0]["title"] == "Deploy windows"
    assert data["skills"] and data["skills"][0]["name"] == "Deploy checklist"
    assert "knowledge" not in data


def test_default_retrieve_keeps_legacy_contract(client, db_session):
    resp = client.post("/api/v1/context/retrieve", json={"query": "anything"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "policy" in data and "retrieval_run_id" in data  # chunks-only shape intact


def test_unified_retrieve_rejects_unknown_source_type(client):
    resp = client.post("/api/v1/context/retrieve", json={"query": "x", "source_types": ["graph"]})
    assert resp.status_code == 400
