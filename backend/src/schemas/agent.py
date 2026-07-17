from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AgentTemplateResponse(BaseModel):
    id: str
    name: str
    role: str
    description: str
    default_config: dict


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = None
    default_model_id: Optional[str] = Field(default=None, min_length=1)
    backup_model_ids: Optional[List[str]] = Field(default_factory=list)
    allowed_tools: Optional[List[str]] = Field(default_factory=list)
    system_prompt: Optional[str] = ""
    output_format: Optional[str] = "markdown"
    max_steps_per_task: Optional[int] = 10
    max_tokens_per_task: Optional[int] = 32000
    max_duration_seconds: Optional[int] = 900
    max_consecutive_failures: Optional[int] = 3
    allow_handoff: Optional[bool] = False
    handoff_threshold_tokens: Optional[int] = None
    template_id: Optional[str] = None

    @field_validator("max_steps_per_task")
    @classmethod
    def validate_max_steps(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("max_steps_per_task must be greater than 0")
        if v is not None and v > 50:
            raise ValueError("max_steps_per_task must not exceed 50")
        return v

    @field_validator("max_tokens_per_task", "max_duration_seconds", "max_consecutive_failures")
    @classmethod
    def validate_positive_limits(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("resource limits must be greater than 0")
        return v

    @field_validator("handoff_threshold_tokens")
    @classmethod
    def validate_threshold(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1000:
            raise ValueError("handoff_threshold_tokens must be at least 1000")
        return v


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    default_model_id: Optional[str] = None
    backup_model_ids: Optional[List[str]] = None
    allowed_tools: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    output_format: Optional[str] = None
    max_steps_per_task: Optional[int] = None
    max_tokens_per_task: Optional[int] = None
    max_duration_seconds: Optional[int] = None
    max_consecutive_failures: Optional[int] = None
    allow_handoff: Optional[bool] = None
    handoff_threshold_tokens: Optional[int] = None

    @field_validator("max_steps_per_task")
    @classmethod
    def validate_max_steps(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("max_steps_per_task must be greater than 0")
        if v is not None and v > 50:
            raise ValueError("max_steps_per_task must not exceed 50")
        return v

    @field_validator("max_tokens_per_task", "max_duration_seconds", "max_consecutive_failures")
    @classmethod
    def validate_positive_limits(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("resource limits must be greater than 0")
        return v

    @field_validator("handoff_threshold_tokens")
    @classmethod
    def validate_threshold(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1000:
            raise ValueError("handoff_threshold_tokens must be at least 1000")
        return v


class AgentStatusUpdate(BaseModel):
    is_enabled: bool


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    description: Optional[str]
    status: str
    current_task_id: Optional[str]
    default_model_id: str
    backup_model_ids: List[str]
    allowed_tools: List[str]
    system_prompt: str
    output_format: Optional[str]
    max_steps_per_task: int
    max_tool_calls_per_task: Optional[int]
    max_tokens_per_task: int
    max_duration_seconds: int
    max_consecutive_failures: int
    allow_handoff: bool
    handoff_threshold_tokens: Optional[int]
    is_enabled: bool
    total_tasks_completed: int
    total_tasks_failed: int
    total_handoffs_initiated: int
    average_tokens_per_task: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]


class AgentListItem(BaseModel):
    id: str
    name: str
    role: str
    description: Optional[str]
    status: str
    default_model_id: str
    is_enabled: bool
    current_task_id: Optional[str]
    total_tasks_completed: int
    created_at: Optional[str]


class AgentListResponse(BaseModel):
    items: List[AgentListItem]
    total: int
    page: int
    page_size: int


class AgentCreateResponse(BaseModel):
    id: str
    name: str
    role: str
    status: str
    created_at: Optional[str]


class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
