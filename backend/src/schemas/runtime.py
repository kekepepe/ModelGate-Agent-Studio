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


class RuntimeStatusResponse(BaseModel):
    goal_id: str
    goal_title: str
    goal_status: str
    current_task_id: Optional[str] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    handoff_tasks: int = 0
    handoff_count: int = 0
    total_tokens_used: int = 0
    log_count: int = 0
    model_call_count: int = 0
    error_count: int = 0
    final_output: Optional[str] = None
    error_message: Optional[str] = None
    quota_status: Optional[str] = None
