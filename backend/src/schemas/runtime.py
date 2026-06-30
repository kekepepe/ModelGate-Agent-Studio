from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionStepResult(BaseModel):
    task_id: str
    status: str
    output: Optional[str] = None
    tokens_used: int = 0
    duration_ms: Optional[int] = None
    model_name: Optional[str] = None
    worker_id: Optional[str] = None
    quota_status: Optional[str] = None
    is_handoff: bool = False


class GoalExecutionResult(BaseModel):
    goal_id: str
    status: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_handoff: int = 0
    total_tokens_used: int = 0
    total_duration_ms: int = 0
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
