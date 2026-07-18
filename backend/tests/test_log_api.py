from fastapi.testclient import TestClient


class TestCreateLog:
    def test_create_log_success(self, client: TestClient, db_session):
        resp = client.post("/api/v1/logs", json={
            "event_type": "model_call",
            "event_status": "completed",
            "goal_id": "goal-1",
            "task_id": "task-1",
            "agent_id": "agent-1",
            "model_id": "gpt-4o",
            "input_summary": "Generate login component",
            "output_summary": "```tsx\nimport React...",
            "token_usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            "latency_ms": 1200,
        })
        assert resp.status_code == 201
        assert resp.json()["success"] is True
        assert "log_id" in resp.json()["data"]

    def test_create_log_invalid_event_type(self, client: TestClient):
        resp = client.post("/api/v1/logs", json={
            "event_type": "invalid_type",
            "event_status": "completed",
        })
        assert resp.status_code == 422


class TestListLogs:
    def test_list_empty(self, client: TestClient):
        resp = client.get("/api/v1/logs")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["items"] == []
        assert data["total"] == 0
        assert data["total_pages"] == 0

    def test_list_with_logs(self, client: TestClient, db_session):
        for i in range(3):
            client.post("/api/v1/logs", json={
                "event_type": "model_call",
                "event_status": "completed",
                "task_id": "task-list",
                "input_summary": f"call {i}",
            })
        resp = client.get("/api/v1/logs")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert "total_pages" in data

    def test_list_filter_event_type(self, client: TestClient, db_session):
        client.post("/api/v1/logs", json={
            "event_type": "model_call",
            "event_status": "completed",
            "input_summary": "model",
        })
        client.post("/api/v1/logs", json={
            "event_type": "error",
            "event_status": "failed",
            "input_summary": "error",
        })
        resp = client.get("/api/v1/logs?event_type=model_call")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 1
        assert data["items"][0]["event_type"] == "model_call"

    def test_list_filter_event_type_multi(self, client: TestClient, db_session):
        client.post("/api/v1/logs", json={
            "event_type": "model_call", "event_status": "completed", "input_summary": "a",
        })
        client.post("/api/v1/logs", json={
            "event_type": "error", "event_status": "failed", "input_summary": "b",
        })
        client.post("/api/v1/logs", json={
            "event_type": "agent_step", "event_status": "completed", "input_summary": "c",
        })
        resp = client.get("/api/v1/logs?event_type=model_call,error")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 2

    def test_list_filter_search(self, client: TestClient, db_session):
        client.post("/api/v1/logs", json={
            "event_type": "model_call", "event_status": "completed", "input_summary": "hello world",
        })
        client.post("/api/v1/logs", json={
            "event_type": "model_call", "event_status": "completed", "input_summary": "foo bar",
        })
        resp = client.get("/api/v1/logs?search=hello")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 1
        assert data["items"][0]["input_summary"] == "hello world"

    def test_list_pagination(self, client: TestClient, db_session):
        for i in range(5):
            client.post("/api/v1/logs", json={
                "event_type": "model_call", "event_status": "completed", "input_summary": f"log-{i}",
            })
        resp = client.get("/api/v1/logs?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["total_pages"] == 3

    def test_list_filter_task_id(self, client: TestClient, db_session):
        client.post("/api/v1/logs", json={
            "event_type": "model_call", "event_status": "completed", "task_id": "t1", "input_summary": "a",
        })
        client.post("/api/v1/logs", json={
            "event_type": "model_call", "event_status": "completed", "task_id": "t2", "input_summary": "b",
        })
        resp = client.get("/api/v1/logs?task_id=t1")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 1
        assert data["items"][0]["task_id"] == "t1"


class TestGetLog:
    def test_get_log_success(self, client: TestClient, db_session):
        create_resp = client.post("/api/v1/logs", json={
            "event_type": "model_call",
            "event_status": "completed",
            "input_summary": "test",
            "token_usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            "metadata": {"latency_ms": 100},
            "routing_info": {"routing_reason": "best_match", "confidence": 0.95},
        })
        log_id = create_resp.json()["data"]["log_id"]
        resp = client.get(f"/api/v1/logs/{log_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == log_id
        assert data["event_type"] == "model_call"
        assert data["token_usage"]["total_tokens"] == 15
        assert data["metadata"]["latency_ms"] == 100
        assert data["routing_info"]["confidence"] == 0.95

    def test_get_log_not_found(self, client: TestClient):
        resp = client.get("/api/v1/logs/nonexistent")
        assert resp.status_code == 404


class TestTaskTimeline:
    def test_timeline_empty(self, client: TestClient):
        resp = client.get("/api/v1/logs/task/task-empty/timeline")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["events"] == []
        assert data["summary"]["total_tokens"] == 0
        assert data["summary"]["model_call_count"] == 0

    def test_timeline_with_events(self, client: TestClient, db_session):
        task_id = "task-tl-1"
        client.post("/api/v1/logs", json={
            "event_type": "model_call", "event_status": "completed", "task_id": task_id,
            "input_summary": "call 1", "token_usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        })
        client.post("/api/v1/logs", json={
            "event_type": "handoff_created", "event_status": "created", "task_id": task_id,
            "input_summary": "handoff",
        })
        client.post("/api/v1/logs", json={
            "event_type": "error", "event_status": "failed", "task_id": task_id,
            "input_summary": "oops", "error_message": "something broke",
        })
        resp = client.get(f"/api/v1/logs/task/{task_id}/timeline")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["events"]) == 3
        assert data["summary"]["total_tokens"] == 150
        assert data["summary"]["model_call_count"] == 1
        assert data["summary"]["handoff_count"] == 1
        assert data["summary"]["error_count"] == 1
        # Events should be in ascending order by time
        assert data["events"][0]["event_type"] == "model_call"
