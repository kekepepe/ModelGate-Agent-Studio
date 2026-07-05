from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ModelBase(BaseModel):
    provider: str = Field(..., min_length=1, max_length=50)
    model_name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    capability_tags: Optional[List[str]] = Field(default_factory=list)
    max_context_tokens: Optional[int] = 8192
    cost_level: Optional[int] = 3
    speed_level: Optional[int] = 3
    is_enabled: Optional[bool] = True
    is_default: Optional[bool] = False
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None

    @field_validator("cost_level")
    @classmethod
    def validate_cost_level(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("cost_level must be between 1 and 5")
        return v

    @field_validator("speed_level")
    @classmethod
    def validate_speed_level(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("speed_level must be between 1 and 5")
        return v

    @field_validator("max_context_tokens")
    @classmethod
    def validate_max_context(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("max_context_tokens must be greater than 0")
        return v


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    provider: Optional[str] = Field(None, min_length=1, max_length=50)
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    capability_tags: Optional[List[str]] = None
    max_context_tokens: Optional[int] = None
    cost_level: Optional[int] = None
    speed_level: Optional[int] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None

    @field_validator("cost_level")
    @classmethod
    def validate_cost_level(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("cost_level must be between 1 and 5")
        return v

    @field_validator("speed_level")
    @classmethod
    def validate_speed_level(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("speed_level must be between 1 and 5")
        return v


class ModelOut(BaseModel):
    id: str
    provider: str
    model_name: str
    display_name: str
    capability_tags: List[str]
    max_context_tokens: int
    cost_level: int
    speed_level: int
    is_enabled: bool
    is_default: bool
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ModelListResponse(BaseModel):
    items: List[ModelOut]
    total: int
    page: int
    page_size: int
    total_pages: int
