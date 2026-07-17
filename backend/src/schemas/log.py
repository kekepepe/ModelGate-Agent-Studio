from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


LOG_EVENT_TYPE_PATTERN = r"^(run\.created|run\.paused|run\.resumed|plan\.created|plan\.updated|task\.created|task\.assigned|task\.started|task\.completed|model_health|model_call|model_stream|agent_step|tool_call|task_status_change|quota_status_change|handoff_created|handoff_completed|memory_retrieved|memory_write_candidate|checkpoint_restored|worktree_created|worktree_merged|verification_started|verification_failed|verification_passed|error|supervisor_review)$"
LOG_EVENT_STATUS_PATTERN = "^(success|failed|error|info|warning|pending|running|completed|cancelled|timeout|rate_limited|quota_exceeded|validation_error|unknown|started|transition|detected|created|accepted|rejected|approved|needs_revision|skipped|denied|retrying|blocked|conflict)$"


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class RoutingInfo(BaseModel):
    routing_reason: Optional[str] = None
    confidence: Optional[float] = None
    risk_flags: List[str] = Field(default_factory=list)


class ExecutionLogCreate(BaseModel):
    goal_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    worker_id: Optional[str] = None
    model_id: Optional[str] = None
    handoff_id: Optional[str] = None
    event_type: str = Field(..., pattern=LOG_EVENT_TYPE_PATTERN)
    event_status: str = Field(..., pattern=LOG_EVENT_STATUS_PATTERN)
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    latency_ms: Optional[int] = None
    error_type: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    tool_name: Optional[str] = None
    quota_status: Optional[str] = None
    handoff_status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    routing_info: Optional[RoutingInfo] = None


class ExecutionLogResponse(BaseModel):
    id: str
    goal_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    worker_id: Optional[str] = None
    model_id: Optional[str] = None
    handoff_id: Optional[str] = None
    event_type: str
    event_status: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    token_usage: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    error_type: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    tool_name: Optional[str] = None
    quota_status: Optional[str] = None
    handoff_status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    routing_info: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    # Enriched fields from joins
    agent_name: Optional[str] = None
    task_title: Optional[str] = None
    model_name: Optional[str] = None


class LogListResponse(BaseModel):
    items: List[ExecutionLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TimelineEvent(BaseModel):
    time: str
    event_type: str
    event_status: str
    agent_id: Optional[str] = None
    model_id: Optional[str] = None
    summary: str
    icon_type: str


class TimelineSummary(BaseModel):
    total_duration_ms: int
    total_tokens: int
    model_call_count: int
    handoff_count: int
    error_count: int


class TaskTimelineResponse(BaseModel):
    events: List[TimelineEvent]
    summary: TimelineSummary
