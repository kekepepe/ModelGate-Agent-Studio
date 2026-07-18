

def _create_agent(client, name, role, model_id="claude-opus-4-7"):
    resp = client.post("/api/v1/agents", json={
        "name": name,
        "role": role,
        "default_model_id": model_id,
    })
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_task(client, agent_id, model_id, status="running", output=None, error=None):
    body = {
        "goal_id": "goal-1",
        "title": "Demo task",
        "description": "A demo handoff task",
        "assigned_agent_id": agent_id,
        "assigned_model_id": model_id,
        "status": status,
    }
    if output is not None:
        body["current_output"] = output
    if error is not None:
        body["error_message"] = error
    resp = client.post("/api/v1/handoff/tasks", json=body)
    assert resp.status_code == 201
    return resp.json()["data"]


class TestCreateDemoTask:
    def test_create_task_creates_worker(self, client):
        agent = _create_agent(client, "Coder", "coder")
        resp = client.post("/api/v1/handoff/tasks", json={
            "goal_id": "goal-1",
            "title": "Demo",
            "description": "Demo",
            "assigned_agent_id": agent,
            "assigned_model_id": "claude-opus-4-7",
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "running"
        assert data["assigned_worker_id"] is not None

    def test_create_task_unknown_agent(self, client):
        resp = client.post("/api/v1/handoff/tasks", json={
            "goal_id": "goal-1",
            "title": "Demo",
            "assigned_agent_id": "missing",
            "assigned_model_id": "x",
        })
        assert resp.status_code == 404


class TestTriggerHandoff:
    def test_trigger_creates_ready_handoff(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task = _create_task(client, from_agent, "claude-opus-4-7")
        resp = client.post(
            f"/api/v1/tasks/{task['id']}/handoff",
            json={"to_agent_id": to_agent, "reason": "manual", "reason_description": "user requested"}
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "ready"
        assert "handoff_id" in data

    def test_trigger_requires_running_or_failed(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task = _create_task(client, from_agent, "claude-opus-4-7", status="completed")
        resp = client.post(
            f"/api/v1/tasks/{task['id']}/handoff",
            json={"to_agent_id": to_agent, "reason": "manual"}
        )
        assert resp.status_code == 400

    def test_duplicate_handoff_returns_409(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task = _create_task(client, from_agent, "claude-opus-4-7")
        body = {"to_agent_id": to_agent, "reason": "manual"}
        first = client.post(f"/api/v1/tasks/{task['id']}/handoff", json=body)
        assert first.status_code == 201
        second = client.post(f"/api/v1/tasks/{task['id']}/handoff", json=body)
        assert second.status_code == 409

    def test_trigger_unknown_task(self, client):
        resp = client.post(
            "/api/v1/tasks/missing/handoff",
            json={"to_agent_id": "x", "reason": "manual"}
        )
        assert resp.status_code == 404


class TestGetHandoff:
    def test_get_handoff_with_summary(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task = _create_task(client, from_agent, "claude-opus-4-7", output="已完成初始分析")
        handoff_id = client.post(
            f"/api/v1/tasks/{task['id']}/handoff",
            json={"to_agent_id": to_agent, "reason": "manual", "reason_description": "user"}
        ).json()["data"]["handoff_id"]
        resp = client.get(f"/api/v1/handoffs/{handoff_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == handoff_id
        assert "handoff_summary" in data
        for key in ["original_goal", "current_task", "completed_work"]:
            assert key in data["handoff_summary"]
        assert data["from_agent_name"] == "Coder"
        assert data["to_agent_name"] == "Reviewer"

    def test_get_handoff_not_found(self, client):
        resp = client.get("/api/v1/handoffs/missing")
        assert resp.status_code == 404


class TestAcceptHandoff:
    def test_accept_creates_worker_and_advances(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task = _create_task(client, from_agent, "claude-opus-4-7")
        handoff_id = client.post(
            f"/api/v1/tasks/{task['id']}/handoff",
            json={"to_agent_id": to_agent, "reason": "manual"}
        ).json()["data"]["handoff_id"]
        resp = client.post(f"/api/v1/handoffs/{handoff_id}/accept", json={})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "accepted"
        assert data["worker_id"]

    def test_accept_invalid_status(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task = _create_task(client, from_agent, "claude-opus-4-7")
        handoff_id = client.post(
            f"/api/v1/tasks/{task['id']}/handoff",
            json={"to_agent_id": to_agent, "reason": "manual"}
        ).json()["data"]["handoff_id"]
        client.post(f"/api/v1/handoffs/{handoff_id}/accept", json={})
        # already accepted
        resp = client.post(f"/api/v1/handoffs/{handoff_id}/accept", json={})
        assert resp.status_code == 400


class TestResultHandoff:
    def test_result_marks_completed(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task = _create_task(client, from_agent, "claude-opus-4-7")
        handoff_id = client.post(
            f"/api/v1/tasks/{task['id']}/handoff",
            json={"to_agent_id": to_agent, "reason": "manual"}
        ).json()["data"]["handoff_id"]
        client.post(f"/api/v1/handoffs/{handoff_id}/accept", json={})
        resp = client.patch(
            f"/api/v1/handoffs/{handoff_id}/result",
            json={"result_after_handoff": "success", "result_note": "done"}
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "completed"
        assert data["result_after_handoff"] == "success"

    def test_result_invalid_enum(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task = _create_task(client, from_agent, "claude-opus-4-7")
        handoff_id = client.post(
            f"/api/v1/tasks/{task['id']}/handoff",
            json={"to_agent_id": to_agent, "reason": "manual"}
        ).json()["data"]["handoff_id"]
        client.post(f"/api/v1/handoffs/{handoff_id}/accept", json={})
        resp = client.patch(
            f"/api/v1/handoffs/{handoff_id}/result",
            json={"result_after_handoff": "unknown"}
        )
        # Pydantic pattern validation
        assert resp.status_code == 422

    def test_result_before_accept(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task = _create_task(client, from_agent, "claude-opus-4-7")
        handoff_id = client.post(
            f"/api/v1/tasks/{task['id']}/handoff",
            json={"to_agent_id": to_agent, "reason": "manual"}
        ).json()["data"]["handoff_id"]
        resp = client.patch(
            f"/api/v1/handoffs/{handoff_id}/result",
            json={"result_after_handoff": "success"}
        )
        assert resp.status_code == 400


class TestListHandoffs:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/handoffs")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_filter_by_status(self, client):
        from_agent = _create_agent(client, "Coder", "coder")
        to_agent = _create_agent(client, "Reviewer", "reviewer", model_id="claude-sonnet-4-6")
        task1 = _create_task(client, from_agent, "claude-opus-4-7")
        task2 = _create_task(client, from_agent, "claude-opus-4-7")
        h1 = client.post(f"/api/v1/tasks/{task1['id']}/handoff", json={"to_agent_id": to_agent, "reason": "manual"}).json()["data"]["handoff_id"]
        client.post(f"/api/v1/tasks/{task2['id']}/handoff", json={"to_agent_id": to_agent, "reason": "quota_exceeded"})
        client.post(f"/api/v1/handoffs/{h1}/accept", json={})
        client.patch(f"/api/v1/handoffs/{h1}/result", json={"result_after_handoff": "success"})
        resp = client.get("/api/v1/handoffs?status=completed")
        assert resp.json()["data"]["total"] == 1
