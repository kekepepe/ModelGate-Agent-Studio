from typing import List, Optional

from pydantic import BaseModel


class DashboardAgentStatus(BaseModel):
    agent_id: str
    name: str
    role: str
    status: str


class DashboardModelUsage(BaseModel):
    model_id: str
    display_name: str
    tokens_used: int
    calls_count: int


class DashboardToolUsage(BaseModel):
    tool_name: str
    call_count: int
    success_count: int
    failed_count: int
    success_rate: float


class DashboardRecentGoal(BaseModel):
    id: str
    title: str
    status: str
    updated_at: Optional[str]


class DashboardStatsResponse(BaseModel):
    active_goals: int
    completed_goals_today: int
    total_tokens_today: int
    total_model_calls_today: int
    total_tool_calls_today: int
    handoffs_today: int
    agents_status: List[DashboardAgentStatus]
    model_usage: List[DashboardModelUsage]
    tool_usage: List[DashboardToolUsage]
    recent_goals: List[DashboardRecentGoal]


class DashboardTrendPoint(BaseModel):
    date: str
    tokens: int
    model_calls: int
    tool_calls: int
    handoffs: int
    tasks_completed: int
    tasks_failed: int
    quota_usage_percent: float


class DashboardTrendsResponse(BaseModel):
    daily: List[DashboardTrendPoint]


class DashboardAgentPerformance(BaseModel):
    agent_id: str
    name: str
    role: str
    tasks_completed: int
    tasks_failed: int
    success_rate: float
    avg_tokens_per_task: int
    avg_duration_ms: int
    total_handoffs_initiated: int


class DashboardAgentPerformanceResponse(BaseModel):
    agents: List[DashboardAgentPerformance]
