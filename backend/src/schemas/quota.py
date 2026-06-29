from typing import List, Optional
from pydantic import BaseModel, Field


class RecordUsageRequest(BaseModel):
    provider: str
    model_id: str
    model_name: Optional[str] = None
    agent_station_id: Optional[str] = None
    task_id: Optional[str] = None
    request_tokens: int = Field(default=0, ge=0)
    response_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    error_code: Optional[int] = None
    error_type: Optional[str] = None


class UpdateQuotaRequest(BaseModel):
    token_limit: Optional[int] = Field(default=None, ge=1)
    request_limit: Optional[int] = Field(default=None, ge=1)
    cost_limit: Optional[float] = Field(default=None, ge=0)
    reset_period: Optional[str] = Field(default=None, pattern="^(daily|weekly|monthly|never)$")
    reset_date: Optional[int] = Field(default=None, ge=1, le=31)


class UpdateStatusRequest(BaseModel):
    quota_status: str = Field(..., pattern="^(normal|warning|near_limit|limited|cooldown|unknown)$")
    reason: Optional[str] = None
    cooldown_until: Optional[str] = None


class QuotaRecordResponse(BaseModel):
    id: str
    provider: str
    model_id: str
    model_name: str
    request_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    limit_error_count: int
    handoff_triggered_count: int
    quota_mode: str
    token_limit: Optional[int]
    request_limit: Optional[int]
    cost_limit: Optional[float]
    reset_period: Optional[str]
    reset_date: Optional[int]
    usage_percent: Optional[float]
    estimated_remaining: Optional[int]
    quota_status: str
    last_used_at: Optional[str]
    cooldown_until: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class QuotaSummary(BaseModel):
    total_models: int
    normal_count: int
    warning_count: int
    near_limit_count: int
    limited_count: int
    cooldown_count: int
    unknown_count: int


class QuotaOverviewItem(BaseModel):
    quota_record_id: str
    provider: str
    model_id: str
    model_name: str
    request_count: int
    total_tokens: int
    quota_status: str
    usage_percent: Optional[float]
    estimated_remaining: Optional[int]
    last_used_at: Optional[str]
    limit_error_count: int
    handoff_triggered_count: int


class QuotaOverviewResponse(BaseModel):
    summary: QuotaSummary
    models: List[QuotaOverviewItem]


class QuotaStatusResponse(BaseModel):
    quota_record_id: str
    provider: str
    model_id: str
    model_name: str
    request_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    last_used_at: Optional[str]
    estimated_remaining: Optional[int]
    quota_status: str
    limit_error_count: int
    cooldown_until: Optional[str]
    handoff_triggered_count: int
    usage_percent: Optional[float]
    quota_mode: str
    token_limit: Optional[int]


class RecordUsageResponse(BaseModel):
    quota_record_id: str
    updated_status: str
    usage_percent: Optional[float]
    estimated_remaining: Optional[int]
    risk_flags: List[str]
