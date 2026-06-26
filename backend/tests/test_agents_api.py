import pytest


class TestListAgents:
    def test_list_agents_empty(self, client):
        resp = client.get("/api/v1/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_list_agents_with_data(self, client):
        client.post("/api/v1/agents", json={
            "name": "Test Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        resp = client.get("/api/v1/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["name"] == "Test Agent"

    def test_list_agents_filter_by_role(self, client):
        client.post("/api/v1/agents", json={
            "name": "Planner",
            "role": "planner",
            "default_model_id": "model-1",
        })
        client.post("/api/v1/agents", json={
            "name": "Coder",
            "role": "coder",
            "default_model_id": "model-1",
        })
        resp = client.get("/api/v1/agents?role=planner")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 1
        assert resp.json()["data"]["items"][0]["role"] == "planner"

    def test_list_agents_filter_by_status(self, client):
        client.post("/api/v1/agents", json={
            "name": "Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        resp = client.get("/api/v1/agents?status=idle")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 1

    def test_list_agents_search(self, client):
        client.post("/api/v1/agents", json={
            "name": "Alpha Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        client.post("/api/v1/agents", json={
            "name": "Beta Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        resp = client.get("/api/v1/agents?search=Alpha")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 1
        assert resp.json()["data"]["items"][0]["name"] == "Alpha Agent"


class TestCreateAgent:
    def test_create_agent_success(self, client):
        resp = client.post("/api/v1/agents", json={
            "name": "New Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["name"] == "New Agent"
        assert data["data"]["status"] == "idle"

    def test_create_agent_missing_name(self, client):
        resp = client.post("/api/v1/agents", json={
            "role": "coder",
            "default_model_id": "model-1",
        })
        assert resp.status_code == 422

    def test_create_agent_missing_role_and_model(self, client):
        resp = client.post("/api/v1/agents", json={
            "name": "Agent",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "BAD_REQUEST"

    def test_create_agent_invalid_role(self, client):
        resp = client.post("/api/v1/agents", json={
            "name": "Agent",
            "role": "invalid_role",
            "default_model_id": "model-1",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "BAD_REQUEST"

    def test_create_agent_missing_model(self, client):
        resp = client.post("/api/v1/agents", json={
            "name": "Agent",
            "role": "coder",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "BAD_REQUEST"

    def test_create_agent_with_template(self, client):
        resp = client.post("/api/v1/agents", json={
            "name": "My Coder",
            "template_id": "coder",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["name"] == "My Coder"

    def test_create_agent_invalid_template(self, client):
        resp = client.post("/api/v1/agents", json={
            "name": "Agent",
            "template_id": "nonexistent",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "BAD_REQUEST"


class TestGetAgent:
    def test_get_agent_success(self, client):
        create_resp = client.post("/api/v1/agents", json={
            "name": "Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        agent_id = create_resp.json()["data"]["id"]
        resp = client.get(f"/api/v1/agents/{agent_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == agent_id

    def test_get_agent_not_found(self, client):
        resp = client.get("/api/v1/agents/nonexistent-id")
        assert resp.status_code == 404


class TestUpdateAgent:
    def test_update_agent_name(self, client):
        create_resp = client.post("/api/v1/agents", json={
            "name": "Old Name",
            "role": "coder",
            "default_model_id": "model-1",
        })
        agent_id = create_resp.json()["data"]["id"]
        resp = client.patch(f"/api/v1/agents/{agent_id}", json={
            "name": "New Name",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "New Name"

    def test_update_agent_not_found(self, client):
        resp = client.patch("/api/v1/agents/nonexistent-id", json={
            "name": "New Name",
        })
        assert resp.status_code == 404

    def test_update_agent_invalid_max_steps(self, client):
        create_resp = client.post("/api/v1/agents", json={
            "name": "Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        agent_id = create_resp.json()["data"]["id"]
        resp = client.patch(f"/api/v1/agents/{agent_id}", json={
            "max_steps_per_task": 0,
        })
        assert resp.status_code == 422

    def test_update_agent_partial(self, client):
        create_resp = client.post("/api/v1/agents", json={
            "name": "Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        agent_id = create_resp.json()["data"]["id"]
        resp = client.patch(f"/api/v1/agents/{agent_id}", json={
            "system_prompt": "New prompt",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["system_prompt"] == "New prompt"
        assert data["name"] == "Agent"


class TestUpdateAgentStatus:
    def test_disable_agent(self, client):
        create_resp = client.post("/api/v1/agents", json={
            "name": "Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        agent_id = create_resp.json()["data"]["id"]
        resp = client.patch(f"/api/v1/agents/{agent_id}/status", json={
            "is_enabled": False,
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["is_enabled"] is False

    def test_enable_agent(self, client):
        create_resp = client.post("/api/v1/agents", json={
            "name": "Agent",
            "role": "coder",
            "default_model_id": "model-1",
        })
        agent_id = create_resp.json()["data"]["id"]
        client.patch(f"/api/v1/agents/{agent_id}/status", json={"is_enabled": False})
        resp = client.patch(f"/api/v1/agents/{agent_id}/status", json={"is_enabled": True})
        assert resp.status_code == 200
        assert resp.json()["data"]["is_enabled"] is True

    def test_update_status_not_found(self, client):
        resp = client.patch("/api/v1/agents/nonexistent-id/status", json={
            "is_enabled": False,
        })
        assert resp.status_code == 404


class TestListTemplates:
    def test_list_templates(self, client):
        resp = client.get("/api/v1/agents/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) == 6
        roles = [t["role"] for t in data["data"]]
        assert "planner" in roles
        assert "coder" in roles
        assert "reviewer" in roles
        assert "research" in roles
        assert "summarizer" in roles
        assert "supervisor" in roles
