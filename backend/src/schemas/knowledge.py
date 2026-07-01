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
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SkillDraftResponse(BaseModel):
    id: str
    source_run_id: Optional[str] = None
    name: str
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
