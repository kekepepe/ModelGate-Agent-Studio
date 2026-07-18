from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryDraftResponse(BaseModel):
    id: str
    source_run_id: Optional[str] = None
    source_goal_id: Optional[str] = None
    type: str
    title: str
    content: str
    confidence: float
    reason: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    human_approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SkillDraftResponse(BaseModel):
    id: str
    source_run_id: Optional[str] = None
    name: str
    version: str = "1.0"
    scenario: Optional[str] = None
    input_requirements: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    recommended_agents: List[str] = Field(default_factory=list)
    recommended_models: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    output_format: Optional[str] = None
    success_criteria: Optional[str] = None
    common_failures: List[str] = Field(default_factory=list)
    status: str
    human_approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    last_used_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class EvolutionSummary(BaseModel):
    memory_drafts: List[MemoryDraftResponse] = Field(default_factory=list)
    skill_drafts: List[SkillDraftResponse] = Field(default_factory=list)
    total_memories: int = 0
    total_skills: int = 0
    pending_review: int = 0


class ApprovalRequest(BaseModel):
    approved: bool = True
    approved_by: str = "user"


class KnowledgeSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field("workspace", pattern="^(workspace|project_document)$")
    uri: str = Field(..., min_length=1, max_length=4000)
    workspace_scope: Optional[str] = Field(None, max_length=2000)
    sync_policy: str = Field("manual", pattern="^(manual|on_start|scheduled)$")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(active|disabled)$")


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    goal_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    token_budget: int = Field(1200, ge=0, le=100000)
    source_ids: List[str] = Field(default_factory=list)
    workspace_scope: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
