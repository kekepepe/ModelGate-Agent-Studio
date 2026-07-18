from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    team_preset: Optional[str] = Field(None, pattern="^(code-delivery|deep-research|document-production|custom-team)$")
    execution_mode: Optional[str] = Field(None, pattern="^(live|sandbox|dry_run|mock)$")
    workspace_root: Optional[str] = None
    budget_tokens: int = Field(100000, gt=0, le=10_000_000)
    budget_cost_usd: Optional[float] = Field(None, gt=0)
    max_duration_seconds: int = Field(3600, gt=0, le=86_400)
    max_parallel_tasks: int = Field(3, gt=0, le=32)


class GoalResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    team_preset: Optional[str] = None
    status: str
    execution_mode: str = "live"
    workspace_root: Optional[str] = None
    final_verification_status: Optional[str] = None
    budget_tokens: int = 100000
    budget_cost_usd: Optional[float] = None
    max_duration_seconds: int = 3600
    max_parallel_tasks: int = 3
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    goal_id: str
    title: str
    description: Optional[str] = None
    status: str
    assigned_agent_id: Optional[str] = None
    assigned_worker_id: Optional[str] = None
    output: Optional[str] = None
    tokens_used: int = 0
    duration_ms: Optional[int] = None
    priority: int = 0
    flow_position: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Enriched fields
    agent_name: Optional[str] = None
    agent_role: Optional[str] = None
    model_name: Optional[str] = None
    worker_status: Optional[str] = None
    workspace_scope: Optional[str] = None
    step_count: int = 0
    failure_count: int = 0
    last_observation: Optional[str] = None
    next_action: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    acceptance_criteria: List[Dict[str, Any]] = Field(default_factory=list)
    verification_status: Optional[str] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    verification_results: List[Dict[str, Any]] = Field(default_factory=list)
    context_runs: List[Dict[str, Any]] = Field(default_factory=list)
    selection_decision: Optional[Dict[str, Any]] = None
    plan_version_id: Optional[str] = None
    plan_task_id: Optional[str] = None
    plan_source: Optional[str] = None


class AgentState(BaseModel):
    id: str
    name: str
    role: str
    status: str
    default_model_id: Optional[str] = None
    is_enabled: bool = True


class WorkerState(BaseModel):
    id: str
    agent_id: str
    model_id: str
    goal_id: Optional[str] = None
    task_id: Optional[str] = None
    inherited_from_handoff_id: Optional[str] = None
    status: str
    total_tokens_used: int = 0
    model_name: Optional[str] = None
    quota_status: Optional[str] = None
    workspace_scope: Optional[str] = None


class WorkspaceState(BaseModel):
    goal: Optional[GoalResponse] = None
    tasks: List[TaskResponse] = Field(default_factory=list)
    agents: List[AgentState] = Field(default_factory=list)
    workers: List[WorkerState] = Field(default_factory=list)
    active_plan: Optional[Dict[str, Any]] = None
    plan_versions: List[Dict[str, Any]] = Field(default_factory=list)
    task_mode: Optional[str] = None
    activation_reason: Optional[str] = None
    task_edges: List[Dict[str, str]] = Field(default_factory=list)
    parallel_groups: List[Dict[str, Any]] = Field(default_factory=list)
    replan_events: List[Dict[str, Any]] = Field(default_factory=list)
    completion_evidence: Optional[Dict[str, Any]] = None
    context_runs: List[Dict[str, Any]] = Field(default_factory=list)
    selection_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    multi_agent_metrics: Optional[Dict[str, Any]] = None


class StartResponse(BaseModel):
    goal_id: str
    status: str


class TaskCancelRequest(BaseModel):
    reason: str = Field("Cancelled by user", min_length=1, max_length=1000)


class TaskSkipRequest(BaseModel):
    reason: str = Field("Skipped by user", min_length=1, max_length=1000)


class TaskSplitRequest(BaseModel):
    titles: List[str] = Field(..., min_length=2, max_length=20)
