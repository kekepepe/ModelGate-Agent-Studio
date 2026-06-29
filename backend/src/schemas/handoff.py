from typing import List, Optional
from pydantic import BaseModel, Field


HANDOFF_STATUS_PATTERN = "^(requested|generating_summary|ready|accepted|completed|failed)$"
HANDOFF_REASON_PATTERN = "^(quota_exceeded|error|quality_issue|role_mismatch|manual|context_limit|other)$"
HANDOFF_RESULT_PATTERN = "^(success|partial|failed)$"
TASK_STATUS_PATTERN = "^(running|failed|handoff|completed|blocked)$"


class HandoffSummary(BaseModel):
    original_goal: str
    current_task: str
    completed_work: List[str]
    unfinished_work: List[str]
    important_constraints: List[str]
    key_decisions: List[str]
    errors_and_risks: List[str]
    next_suggested_steps: List[str]
    context_needed: List[str]


class HandoffTriggerRequest(BaseModel):
    to_agent_id: str = Field(..., min_length=1)
    to_model_id: Optional[str] = None
    reason: str = Field(..., pattern=HANDOFF_REASON_PATTERN)
    reason_description: Optional[str] = None
    include_recent_logs: bool = True
    include_current_output: bool = True


class HandoffAcceptRequest(BaseModel):
    agent_id: Optional[str] = None
    model_id: Optional[str] = None
    auto_continue: bool = True


class HandoffResultRequest(BaseModel):
    result_after_handoff: str = Field(..., pattern=HANDOFF_RESULT_PATTERN)
    status: Optional[str] = Field(default="completed", pattern="^(completed)$")
    result_note: Optional[str] = None


class HandoffTaskCreate(BaseModel):
    goal_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    status: str = Field(default="running", pattern=TASK_STATUS_PATTERN)
    assigned_agent_id: str = Field(..., min_length=1)
    assigned_model_id: str = Field(..., min_length=1)
    current_output: Optional[str] = None
    error_message: Optional[str] = None


class HandoffTaskResponse(BaseModel):
    id: str
    goal_id: str
    title: str
    description: str
    status: str
    assigned_agent_id: str
    assigned_model_id: str
    assigned_worker_id: Optional[str]
    current_output: Optional[str]
    error_message: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class WorkerSessionResponse(BaseModel):
    id: str
    agent_id: str
    model_id: str
    goal_id: str
    task_id: str
    inherited_from_handoff_id: Optional[str]
    status: str
    current_context: Optional[str]
    final_output: Optional[str]
    error_message: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class ExecutionLogResponse(BaseModel):
    id: str
    goal_id: Optional[str]
    task_id: Optional[str]
    agent_id: Optional[str]
    worker_id: Optional[str]
    model_id: Optional[str]
    handoff_id: Optional[str]
    level: str
    action: str
    message: str
    created_at: Optional[str]


class HandoffRecordResponse(BaseModel):
    id: str
    goal_id: str
    task_id: str
    from_agent_id: str
    from_model_id: str
    from_worker_id: Optional[str]
    to_agent_id: str
    to_model_id: str
    to_worker_id: Optional[str]
    reason: str
    reason_description: Optional[str]
    handoff_summary: HandoffSummary
    status: str
    result_after_handoff: Optional[str]
    result_note: Optional[str]
    tokens_before_handoff: int
    tokens_after_handoff: int
    time_saved_estimate_ms: Optional[int]
    error_message: Optional[str]
    created_at: Optional[str]
    summary_generated_at: Optional[str]
    accepted_at: Optional[str]
    completed_at: Optional[str]
    updated_at: Optional[str]
    task: Optional[HandoffTaskResponse] = None
    from_agent_name: Optional[str] = None
    from_agent_role: Optional[str] = None
    to_agent_name: Optional[str] = None
    to_agent_role: Optional[str] = None
    worker: Optional[WorkerSessionResponse] = None


class HandoffListItem(BaseModel):
    id: str
    goal_id: str
    task_id: str
    task_title: Optional[str]
    from_agent_id: str
    from_agent_name: Optional[str]
    from_model_id: str
    to_agent_id: str
    to_agent_name: Optional[str]
    to_model_id: str
    reason: str
    status: str
    result_after_handoff: Optional[str]
    created_at: Optional[str]


class HandoffListResponse(BaseModel):
    items: List[HandoffListItem]
    total: int
    page: int
    page_size: int


class HandoffTriggerResponse(BaseModel):
    handoff_id: str
    task_id: str
    status: str
    message: str


class HandoffAcceptResponse(BaseModel):
    handoff_id: str
    worker_id: str
    task_id: str
    status: str


class HandoffResultResponse(BaseModel):
    handoff_id: str
    status: str
    result_after_handoff: str


class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
