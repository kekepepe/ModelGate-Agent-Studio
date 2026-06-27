import pytest


class TestSelectModelAPI:
    def test_select_model_success(self, client, db_session):
        # Seed models
        from src.models.model import Model
        m = Model(
            id="model-test",
            provider="test",
            model_name="test-model",
            display_name="Test Model",
            max_context_tokens=100000,
            cost_level=3,
            speed_level=3,
            is_enabled=True,
        )
        m.set_capability_tags(["code", "reasoning"])
        db_session.add(m)
        db_session.commit()

        resp = client.post("/api/v1/router/select-model", json={
            "task_id": "task-1",
            "task_type": "coding",
            "context_length_estimate": 8000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["selected_model_id"]
        assert "confidence" in data["data"]
        assert "routing_reason" in data["data"]
        assert "score_breakdown" in data["data"]

    def test_select_model_no_eligible_models(self, client):
        resp = client.post("/api/v1/router/select-model", json={
            "task_id": "task-1",
            "task_type": "coding",
            "required_capabilities": ["nonexistent"],
            "context_length_estimate": 8000,
        })
        assert resp.status_code == 503
        data = resp.json()
        assert data["detail"]["error"]["code"] == "NO_ELIGIBLE_MODEL"

    def test_select_model_missing_task_id(self, client):
        resp = client.post("/api/v1/router/select-model", json={
            "task_type": "coding",
        })
        assert resp.status_code == 422

    def test_select_model_user_override(self, client, db_session):
        from src.models.model import Model
        m = Model(
            id="model-override",
            provider="test",
            model_name="override-model",
            display_name="Override Model",
            max_context_tokens=100000,
            cost_level=3,
            speed_level=3,
            is_enabled=True,
        )
        m.set_capability_tags(["code", "reasoning"])
        db_session.add(m)
        db_session.commit()

        resp = client.post("/api/v1/router/select-model", json={
            "task_id": "task-1",
            "task_type": "coding",
            "preferred_model_id": "model-override",
            "context_length_estimate": 8000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["selected_model_id"] == "model-override"
        assert data["data"]["is_user_override"] is True

    def test_select_model_excludes_disabled(self, client, db_session):
        from src.models.model import Model
        enabled = Model(
            id="model-enabled",
            provider="test",
            model_name="enabled",
            display_name="Enabled Model",
            max_context_tokens=100000,
            cost_level=3,
            speed_level=3,
            is_enabled=True,
        )
        enabled.set_capability_tags(["code", "reasoning"])
        disabled = Model(
            id="model-disabled-api",
            provider="test",
            model_name="disabled",
            display_name="Disabled Model",
            max_context_tokens=100000,
            cost_level=3,
            speed_level=3,
            is_enabled=False,
        )
        disabled.set_capability_tags(["code", "reasoning"])
        db_session.add_all([enabled, disabled])
        db_session.commit()

        resp = client.post("/api/v1/router/select-model", json={
            "task_id": "task-1",
            "task_type": "coding",
            "context_length_estimate": 8000,
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["selected_model_id"] == "model-enabled"


class TestOverrideModelAPI:
    def test_override_success(self, client, db_session):
        from src.models.model import Model
        m = Model(
            id="model-backup",
            provider="test",
            model_name="backup-model",
            display_name="Backup Model",
            max_context_tokens=100000,
            cost_level=3,
            speed_level=3,
            is_enabled=True,
        )
        m.set_capability_tags(["code"])
        db_session.add(m)
        db_session.commit()

        resp = client.post("/api/v1/router/override-model", json={
            "task_id": "task-1",
            "selected_model_id": "model-backup",
            "reason": "User prefers this model",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["is_user_override"] is True

    def test_override_disabled_model(self, client, db_session):
        from src.models.model import Model
        m = Model(
            id="model-disabled-override",
            provider="test",
            model_name="disabled",
            display_name="Disabled",
            max_context_tokens=100000,
            cost_level=3,
            speed_level=3,
            is_enabled=False,
        )
        db_session.add(m)
        db_session.commit()

        resp = client.post("/api/v1/router/override-model", json={
            "task_id": "task-1",
            "selected_model_id": "model-disabled-override",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "BAD_REQUEST"


class TestGetRoutingRulesAPI:
    def test_get_rules(self, client):
        resp = client.get("/api/v1/router/rules")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "weights" in data["data"]
        assert "role_preferences" in data["data"]
        assert "hard_constraints" in data["data"]
        weights = data["data"]["weights"]
        assert abs(sum(weights.values()) - 1.0) < 0.01
