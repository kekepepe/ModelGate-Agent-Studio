from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SupervisorReviewResponse(BaseModel):
    id: str
    goal_id: str
    run_id: Optional[str] = None
    status: str
    summary: Optional[str] = None
    issues: List[str] = Field(default_factory=list)
    suggested_tasks: List[Dict[str, str]] = Field(default_factory=list)
    passed: bool = False
    reviewer_agent_id: Optional[str] = None
    reviewer_model_id: Optional[str] = None
    tokens_used: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
