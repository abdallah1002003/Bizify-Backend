from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class ComparisonMetricBase(BaseModel):
    comparison_id: UUID
    metric_name: str
    value: float

class ComparisonMetricCreate(BaseModel):
    comparison_id: UUID
    metric_name: str = Field(..., max_length=255)
    value: float

class ComparisonMetricUpdate(BaseModel):
    comparison_id: Optional[UUID] = None
    metric_name: Optional[str] = None
    value: Optional[float] = None

class ComparisonMetricResponse(ComparisonMetricBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
