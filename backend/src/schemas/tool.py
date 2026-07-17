from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ToolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    category: str = Field(default="其他", min_length=1, max_length=50)
    risk_level: str = Field(default="low", pattern=r"^(low|medium|high)$")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = True


class ToolUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    risk_level: Optional[str] = Field(None, pattern=r"^(low|medium|high)$")
    parameters: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class ToolOut(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    category: str
    risk_level: str
    parameters: Dict[str, Any]
    is_enabled: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ToolListResponse(BaseModel):
    items: List[ToolOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class ToolCallRecordOut(BaseModel):
    id: str
    goal_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    worker_id: Optional[str] = None
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[str] = None
    status: str
    latency_ms: int
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    result: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ToolCallListResponse(BaseModel):
    items: List[ToolCallRecordOut]
    total: int
    page: int
    page_size: int
    total_pages: int
