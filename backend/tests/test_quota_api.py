

class TestRecordUsage:
    def test_record_usage_creates_new_record(self, client):
        resp = client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "model_name": "GPT-4o",
            "total_tokens": 1000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["updated_status"] == "normal"

    def test_record_usage_accumulates_tokens(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 1000,
        })
        resp = client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 500,
        })
        data = resp.json()
        assert data["data"]["updated_status"] == "normal"
        # Verify via overview
        overview = client.get("/api/v1/quota/overview").json()
        assert overview["data"]["models"][0]["limit_error_count"] == 0
        # Verify via status endpoint for total_tokens
        status = client.get("/api/v1/quota/models/gpt-4o/status").json()
        assert status["data"]["total_tokens"] == 1500

    def test_record_usage_with_limit_error(self, client):
        resp = client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "error_code": 429,
            "error_type": "rate_limit_exceeded",
        })
        data = resp.json()
        assert data["data"]["updated_status"] == "cooldown"
        assert "rate_limited" in data["data"]["risk_flags"]

    def test_record_usage_with_quota_error(self, client):
        resp = client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "error_code": 402,
            "error_type": "insufficient_quota",
        })
        data = resp.json()
        assert data["data"]["updated_status"] == "limited"


class TestGetOverview:
    def test_overview_empty(self, client):
        resp = client.get("/api/v1/quota/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["summary"]["total_models"] == 0
        assert data["data"]["models"] == []

    def test_overview_with_records(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 1000,
        })
        resp = client.get("/api/v1/quota/overview")
        data = resp.json()
        assert data["data"]["summary"]["total_models"] == 1
        assert data["data"]["models"][0]["model_id"] == "gpt-4o"

    def test_overview_filter_by_provider(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 1000,
        })
        client.post("/api/v1/quota/record-usage", json={
            "provider": "anthropic",
            "model_id": "claude-3",
            "total_tokens": 500,
        })
        resp = client.get("/api/v1/quota/overview?provider=openai")
        data = resp.json()
        assert data["data"]["summary"]["total_models"] == 1
        assert data["data"]["models"][0]["provider"] == "openai"

    def test_overview_filter_by_status(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "error_code": 429,
            "error_type": "rate_limit_exceeded",
        })
        client.post("/api/v1/quota/record-usage", json={
            "provider": "anthropic",
            "model_id": "claude-3",
            "total_tokens": 500,
        })
        resp = client.get("/api/v1/quota/overview?status=cooldown")
        data = resp.json()
        assert data["data"]["summary"]["total_models"] == 1
        assert data["data"]["models"][0]["quota_status"] == "cooldown"


class TestGetModelStatus:
    def test_model_status_found(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 1000,
        })
        resp = client.get("/api/v1/quota/models/gpt-4o/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["model_id"] == "gpt-4o"

    def test_model_status_not_found(self, client):
        resp = client.get("/api/v1/quota/models/nonexistent/status")
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"]["error"]["code"] == "NOT_FOUND"


class TestUpdateQuotaConfig:
    def test_update_quota_config_success(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 5000,
        })
        resp = client.patch("/api/v1/quota/models/gpt-4o/quota", json={
            "token_limit": 10000,
            "reset_period": "monthly",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["token_limit"] == 10000
        assert data["data"]["quota_mode"] == "known"
        assert data["data"]["usage_percent"] == 0.5

    def test_update_quota_config_not_found(self, client):
        resp = client.patch("/api/v1/quota/models/nonexistent/quota", json={
            "token_limit": 10000,
        })
        assert resp.status_code == 404

    def test_update_quota_config_invalid_limit(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 1000,
        })
        resp = client.patch("/api/v1/quota/models/gpt-4o/quota", json={
            "token_limit": 0,
        })
        # Pydantic schema validates ge=1, so it returns 422 before reaching service
        assert resp.status_code == 422


class TestUpdateQuotaStatus:
    def test_update_status_success(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 1000,
        })
        resp = client.patch("/api/v1/quota/models/gpt-4o/status", json={
            "quota_status": "normal",
            "reason": "manual reset",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["quota_status"] == "normal"

    def test_update_status_cannot_set_limited(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 1000,
        })
        resp = client.patch("/api/v1/quota/models/gpt-4o/status", json={
            "quota_status": "limited",
        })
        assert resp.status_code == 400

    def test_update_status_not_found(self, client):
        resp = client.patch("/api/v1/quota/models/nonexistent/status", json={
            "quota_status": "normal",
        })
        assert resp.status_code == 404


class TestCheckIntercept:
    def test_intercept_limited_model(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "error_code": 402,
            "error_type": "insufficient_quota",
        })
        resp = client.get("/api/v1/quota/models/gpt-4o/intercept")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["intercepted"] is True

    def test_intercept_normal_model(self, client):
        client.post("/api/v1/quota/record-usage", json={
            "provider": "openai",
            "model_id": "gpt-4o",
            "total_tokens": 1000,
        })
        resp = client.get("/api/v1/quota/models/gpt-4o/intercept")
        data = resp.json()
        assert data["data"]["intercepted"] is False

    def test_intercept_unknown_model(self, client):
        resp = client.get("/api/v1/quota/models/nonexistent/intercept")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["intercepted"] is False
