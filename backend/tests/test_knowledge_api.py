import uuid
from fastapi.testclient import TestClient


def _seed_knowledge_data(db_session):
    from src.models.agent import AgentStation
    from src.models.workspace import Goal, Task
    planner = AgentStation(id=str(uuid.uuid4()), name="Planner", role="planner",
                           default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True)
    db_session.add(planner)
    db_session.commit()
    goal = Goal(id=str(uuid.uuid4()), title="Knowledge Test", status="completed")
    db_session.add(goal)
    db_session.commit()
    t1 = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="T1", status="completed",
              assigned_agent_id=planner.id, output="Done", tokens_used=100)
    t2 = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="T2", status="completed",
              assigned_agent_id=planner.id, output="Done too", tokens_used=200)
    db_session.add_all([t1, t2])
    db_session.commit()
    return goal


class TestKnowledgeAPI:
    def test_generate_memories(self, client: TestClient, db_session):
        goal = _seed_knowledge_data(db_session)
        resp = client.post(f"/api/v1/knowledge/generate/{goal.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_memories"] >= 1
        assert data["total_skills"] >= 1
        assert data["pending_review"] >= 1

    def test_get_evolution(self, client: TestClient, db_session):
        goal = _seed_knowledge_data(db_session)
        client.post(f"/api/v1/knowledge/generate/{goal.id}")
        resp = client.get("/api/v1/knowledge/evolution")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_memories"] >= 1

    def test_approve_memory(self, client: TestClient, db_session):
        goal = _seed_knowledge_data(db_session)
        gen = client.post(f"/api/v1/knowledge/generate/{goal.id}")
        mem_id = gen.json()["data"]["memory_drafts"][0]["id"]
        resp = client.post(f"/api/v1/knowledge/memories/{mem_id}/approve", json={"approved": True, "approved_by": "tester"})
        assert resp.status_code == 200
        assert resp.json()["data"]["human_approved"] is True

    def test_approve_skill(self, client: TestClient, db_session):
        goal = _seed_knowledge_data(db_session)
        gen = client.post(f"/api/v1/knowledge/generate/{goal.id}")
        skills = gen.json()["data"]["skill_drafts"]
        if skills:
            skill_id = skills[0]["id"]
            resp = client.post(f"/api/v1/knowledge/skills/{skill_id}/approve", json={"approved": True, "approved_by": "tester"})
            assert resp.status_code == 200
            assert resp.json()["data"]["human_approved"] is True
