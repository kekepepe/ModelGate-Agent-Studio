from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class GoalResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
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


class WorkspaceState(BaseModel):
    goal: Optional[GoalResponse] = None
    tasks: List[TaskResponse] = Field(default_factory=list)
    agents: List[AgentState] = Field(default_factory=list)
    workers: List[WorkerState] = Field(default_factory=list)


class StartResponse(BaseModel):
    goal_id: str
    status: str
