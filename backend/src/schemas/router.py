from typing import List, Optional
from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    dimension: str
    score: float = Field(..., ge=0.0, le=1.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted_score: float
    reason: str


class ScoreBreakdown(BaseModel):
    model_id: str
    model_name: str
    total_score: float
    dimension_scores: List[DimensionScore]


class RoutingReason(BaseModel):
    summary: str
    primary_factors: List[str]
    secondary_factors: List[str]
    tradeoffs: List[str]


class RiskFlag(BaseModel):
    type: str
    severity: str
    message: str
    suggestion: Optional[str] = None


class RoutingRequest(BaseModel):
    task_id: str
    goal_id: Optional[str] = None
    task_type: str = Field(..., description="e.g. planning, coding, review, research, summarization, supervision, debugging, documentation, testing, general")
    task_complexity: str = Field(default="moderate", description="simple | moderate | complex | very_complex")
    task_description: Optional[str] = None
    required_capabilities: Optional[List[str]] = Field(default_factory=list)
    preferred_agent_id: Optional[str] = None
    preferred_model_id: Optional[str] = None
    context_length_estimate: int = Field(default=8000, ge=0)
    has_vision_input: bool = False
    requires_tool_calling: bool = False
    budget_preference: str = Field(default="medium", description="low | medium | high | unlimited")
    speed_preference: str = Field(default="balanced", description="fast | balanced | quality")


class RoutingResult(BaseModel):
    selected_model_id: str
    selected_agent_id: Optional[str] = None
    backup_model_ids: List[str]
    routing_reason: RoutingReason
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_flags: List[RiskFlag]
    score_breakdown: List[ScoreBreakdown]
    is_user_override: bool = False
    override_note: Optional[str] = None


class OverrideRequest(BaseModel):
    task_id: str
    selected_model_id: str
    original_model_id: Optional[str] = None
    reason: Optional[str] = None


class OverrideResponse(BaseModel):
    task_id: str
    selected_model_id: str
    is_user_override: bool = True
    override_note: Optional[str] = None


class RoutingRulesResponse(BaseModel):
    weights: dict
    role_preferences: dict
    hard_constraints: List[str]


class AgentSelectionRequest(BaseModel):
    task_id: str
    goal_id: Optional[str] = None
    task_type: str = "general"
    risk_level: str = Field("low", pattern="^(low|medium|high)$")
    required_capabilities: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    workspace_scope: Optional[str] = None
    input_type: str = "text"
    output_type: str = "text"
    context_length_estimate: int = Field(8000, ge=0)
