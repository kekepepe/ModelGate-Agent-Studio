"""Tests for Tool Registry API endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestListTools:
    def test_list_tools_empty(self, client: TestClient):
        resp = client.get("/api/v1/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"]["items"], list)

    def test_list_tools_with_filters(self, client: TestClient):
        resp = client.get("/api/v1/tools?category=文件操作")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["data"]["items"]:
            assert item["category"] == "文件操作"

    def test_list_tools_pagination(self, client: TestClient):
        resp = client.get("/api/v1/tools?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 2


class TestCreateTool:
    def test_create_tool_success(self, client: TestClient):
        resp = client.post("/api/v1/tools", json={
            "name": "web_search",
            "display_name": "网络搜索",
            "description": "Search the web",
            "category": "网络",
            "risk_level": "low",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["name"] == "web_search"
        assert data["data"]["display_name"] == "网络搜索"

    def test_create_tool_duplicate_name(self, client: TestClient):
        client.post("/api/v1/tools", json={
            "name": "custom_tool",
            "display_name": "Custom Tool",
            "category": "其他",
            "risk_level": "low",
            "parameters": {},
        })
        resp = client.post("/api/v1/tools", json={
            "name": "custom_tool",
            "display_name": "Custom Tool V2",
            "category": "其他",
            "risk_level": "low",
            "parameters": {},
        })
        assert resp.status_code == 409

    def test_create_tool_invalid_risk_level(self, client: TestClient):
        resp = client.post("/api/v1/tools", json={
            "name": "bad_tool",
            "display_name": "Bad",
            "risk_level": "critical",
            "parameters": {},
        })
        assert resp.status_code == 422


class TestGetTool:
    def test_get_tool_success(self, client: TestClient):
        create = client.post("/api/v1/tools", json={
            "name": "get_test_tool",
            "display_name": "Get Test",
            "category": "测试",
            "risk_level": "medium",
            "parameters": {},
        })
        tool_id = create.json()["data"]["id"]
        resp = client.get(f"/api/v1/tools/{tool_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "get_test_tool"

    def test_get_tool_not_found(self, client: TestClient):
        resp = client.get("/api/v1/tools/nonexistent-id")
        assert resp.status_code == 404


class TestUpdateTool:
    def test_update_tool_success(self, client: TestClient):
        create = client.post("/api/v1/tools", json={
            "name": "update_test_tool",
            "display_name": "Update Test",
            "category": "测试",
            "risk_level": "low",
            "parameters": {},
        })
        tool_id = create.json()["data"]["id"]
        resp = client.put(f"/api/v1/tools/{tool_id}", json={
            "display_name": "Updated Tool",
            "risk_level": "high",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["display_name"] == "Updated Tool"
        assert resp.json()["data"]["risk_level"] == "high"

    def test_update_tool_not_found(self, client: TestClient):
        resp = client.put("/api/v1/tools/nonexistent-id", json={"display_name": "N/A"})
        assert resp.status_code == 404


class TestDeleteTool:
    def test_delete_tool_success(self, client: TestClient):
        create = client.post("/api/v1/tools", json={
            "name": "delete_test_tool",
            "display_name": "Delete Test",
            "category": "测试",
            "risk_level": "low",
            "parameters": {},
        })
        tool_id = create.json()["data"]["id"]
        resp = client.delete(f"/api/v1/tools/{tool_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

        get_resp = client.get(f"/api/v1/tools/{tool_id}")
        assert get_resp.status_code == 404

    def test_delete_tool_not_found(self, client: TestClient):
        resp = client.delete("/api/v1/tools/nonexistent-id")
        assert resp.status_code == 404


class TestToggleTool:
    def test_toggle_tool(self, client: TestClient):
        create = client.post("/api/v1/tools", json={
            "name": "toggle_test_tool",
            "display_name": "Toggle Test",
            "category": "测试",
            "risk_level": "low",
            "parameters": {},
        })
        tool_id = create.json()["data"]["id"]
        resp = client.patch(f"/api/v1/tools/{tool_id}/toggle")
        assert resp.status_code == 200
        assert resp.json()["data"]["is_enabled"] is False

        resp2 = client.patch(f"/api/v1/tools/{tool_id}/toggle")
        assert resp2.status_code == 200
        assert resp2.json()["data"]["is_enabled"] is True

    def test_toggle_tool_not_found(self, client: TestClient):
        resp = client.patch("/api/v1/tools/nonexistent-id/toggle")
        assert resp.status_code == 404


class TestToolCalls:
    def test_list_tool_calls_empty(self, client: TestClient):
        resp = client.get("/api/v1/tools/calls")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"]["items"], list)

    def test_list_tool_calls_with_filter(self, client: TestClient):
        resp = client.get("/api/v1/tools/calls?task_id=some-task&tool_name=file_read")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_get_tool_call_not_found(self, client: TestClient):
        resp = client.get("/api/v1/tools/calls/nonexistent-id")
        assert resp.status_code == 404
