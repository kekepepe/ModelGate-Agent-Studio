import pytest


class TestListModels:
    def test_list_models_empty(self, client):
        resp = client.get("/api/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_list_models_with_data(self, client):
        client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4-turbo",
            "display_name": "GPT-4 Turbo",
            "cost_level": 4,
            "speed_level": 3,
        })
        resp = client.get("/api/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["display_name"] == "GPT-4 Turbo"

    def test_list_models_filter_by_provider(self, client):
        client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "GPT-4",
        })
        client.post("/api/v1/models", json={
            "provider": "anthropic",
            "model_name": "claude-3-opus",
            "display_name": "Claude 3 Opus",
        })
        resp = client.get("/api/v1/models?provider=openai")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 1
        assert resp.json()["data"]["items"][0]["provider"] == "openai"

    def test_list_models_search(self, client):
        client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "GPT-4",
        })
        client.post("/api/v1/models", json={
            "provider": "anthropic",
            "model_name": "claude-3-haiku",
            "display_name": "Claude 3 Haiku",
        })
        resp = client.get("/api/v1/models?search=Claude")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 1
        assert resp.json()["data"]["items"][0]["display_name"] == "Claude 3 Haiku"


class TestCreateModel:
    def test_create_model_success(self, client):
        resp = client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4-turbo",
            "display_name": "GPT-4 Turbo",
            "cost_level": 4,
            "speed_level": 3,
            "capability_tags": ["coding", "reasoning"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["display_name"] == "GPT-4 Turbo"
        assert data["data"]["cost_level"] == 4
        assert data["data"]["capability_tags"] == ["coding", "reasoning"]

    def test_create_model_duplicate_name(self, client):
        client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "GPT-4",
        })
        resp = client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4-other",
            "display_name": "GPT-4",
        })
        assert resp.status_code == 409

    def test_create_model_invalid_cost_level(self, client):
        resp = client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "GPT-4",
            "cost_level": 10,
        })
        assert resp.status_code == 422


class TestGetModel:
    def test_get_model_success(self, client):
        create_resp = client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "GPT-4",
        })
        model_id = create_resp.json()["data"]["id"]
        resp = client.get(f"/api/v1/models/{model_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == model_id

    def test_get_model_not_found(self, client):
        resp = client.get("/api/v1/models/nonexistent-id")
        assert resp.status_code == 404


class TestUpdateModel:
    def test_update_model_success(self, client):
        create_resp = client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "GPT-4",
            "cost_level": 4,
        })
        model_id = create_resp.json()["data"]["id"]
        resp = client.put(f"/api/v1/models/{model_id}", json={
            "display_name": "GPT-4 Updated",
            "cost_level": 3,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["display_name"] == "GPT-4 Updated"
        assert data["data"]["cost_level"] == 3

    def test_update_model_not_found(self, client):
        resp = client.put("/api/v1/models/nonexistent-id", json={
            "display_name": "Updated",
        })
        assert resp.status_code == 404


class TestDeleteModel:
    def test_delete_model_success(self, client):
        create_resp = client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "GPT-4",
        })
        model_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"/api/v1/models/{model_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

        # Verify it's gone
        get_resp = client.get(f"/api/v1/models/{model_id}")
        assert get_resp.status_code == 404

    def test_delete_model_not_found(self, client):
        resp = client.delete("/api/v1/models/nonexistent-id")
        assert resp.status_code == 404


class TestToggleModel:
    def test_toggle_model_enable_disable(self, client):
        create_resp = client.post("/api/v1/models", json={
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "GPT-4",
            "is_enabled": True,
        })
        model_id = create_resp.json()["data"]["id"]

        resp = client.patch(f"/api/v1/models/{model_id}/toggle")
        assert resp.status_code == 200
        assert resp.json()["data"]["is_enabled"] is False

        resp2 = client.patch(f"/api/v1/models/{model_id}/toggle")
        assert resp2.status_code == 200
        assert resp2.json()["data"]["is_enabled"] is True

    def test_toggle_model_not_found(self, client):
        resp = client.patch("/api/v1/models/nonexistent-id/toggle")
        assert resp.status_code == 404
