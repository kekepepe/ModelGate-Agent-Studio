from datetime import datetime, timezone

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord
from src.models.quota import QuotaRecord
from src.models.tool import ToolCallRecord
from src.models.workspace import Goal, Task


class TestDashboardStats:
    def test_dashboard_stats_empty(self, client):
        resp = client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["active_goals"] == 0
        assert data["data"]["model_usage"] == []
        assert data["data"]["tool_usage"] == []

    def test_dashboard_stats_with_data(self, client, db_session):
        now = datetime.now(timezone.utc)
        agent = AgentStation(
            id="agent-1",
            name="Coder",
            role="coder",
            default_model_id="model-1",
            status="running",
        )
        goal = Goal(id="goal-1", title="Build dashboard", status="done", updated_at=now)
        quota = QuotaRecord(
            provider="openai",
            model_id="model-1",
            model_name="GPT-4o",
            request_count=2,
            total_tokens=1500,
            usage_percent=0.4,
        )
        log = ExecutionLog(event_type="model_call", event_status="completed", created_at=now)
        log.set_token_usage({"total_tokens": 300})
        tool_call = ToolCallRecord(
            goal_id="goal-1",
            task_id="task-1",
            agent_id="agent-1",
            worker_id="worker-1",
            tool_name="file_read",
            status="completed",
            latency_ms=10,
            created_at=now,
        )
        tool_call.set_tool_input({"path": "README.md"})
        handoff = HandoffRecord(
            goal_id="goal-1",
            task_id="task-1",
            from_agent_id="agent-1",
            from_model_id="model-1",
            to_agent_id="agent-2",
            to_model_id="model-2",
            reason="quota_risk",
            created_at=now,
        )
        db_session.add_all([agent, goal, quota, log, tool_call, handoff])
        db_session.commit()

        resp = client.get("/api/v1/dashboard/stats")
        data = resp.json()["data"]
        assert data["completed_goals_today"] == 1
        assert data["total_tokens_today"] == 300
        assert data["total_model_calls_today"] == 1
        assert data["total_tool_calls_today"] == 1
        assert data["handoffs_today"] == 1
        assert data["agents_status"][0]["name"] == "Coder"
        assert data["model_usage"][0]["tokens_used"] == 1500
        assert data["tool_usage"][0]["success_rate"] == 1.0


class TestDashboardTrends:
    def test_dashboard_trends_default(self, client):
        resp = client.get("/api/v1/dashboard/trends")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["daily"]) == 7
        assert data["daily"][-1]["tokens"] == 0

    def test_dashboard_trends_days_param(self, client):
        resp = client.get("/api/v1/dashboard/trends?days=3")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["daily"]) == 3


class TestAgentPerformance:
    def test_agent_performance_empty(self, client):
        resp = client.get("/api/v1/dashboard/agent-performance")
        assert resp.status_code == 200
        assert resp.json()["data"]["agents"] == []

    def test_agent_performance_with_tasks(self, client, db_session):
        agent = AgentStation(
            id="agent-1",
            name="Coder",
            role="coder",
            default_model_id="model-1",
            total_handoffs_initiated=1,
        )
        completed = Task(
            id="task-1",
            goal_id="goal-1",
            title="Done",
            status="done",
            assigned_agent_id="agent-1",
            tokens_used=1000,
            duration_ms=2000,
        )
        failed = Task(
            id="task-2",
            goal_id="goal-1",
            title="Failed",
            status="failed",
            assigned_agent_id="agent-1",
            tokens_used=500,
            duration_ms=1000,
        )
        db_session.add_all([agent, completed, failed])
        db_session.commit()

        resp = client.get("/api/v1/dashboard/agent-performance")
        item = resp.json()["data"]["agents"][0]
        assert item["tasks_completed"] == 1
        assert item["tasks_failed"] == 1
        assert item["success_rate"] == 0.5
        assert item["avg_tokens_per_task"] == 750
        assert item["avg_duration_ms"] == 1500
