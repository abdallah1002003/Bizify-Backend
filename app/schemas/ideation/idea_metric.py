from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class IdeaMetricBase(BaseModel):
    idea_id: UUID
    created_by: UUID
    name: str
    value: float
    type: str

class IdeaMetricCreate(BaseModel):
    idea_id: UUID
    created_by: UUID
    name: str = Field(..., max_length=255)
    value: float
    type: str = Field(..., max_length=255)

class IdeaMetricUpdate(BaseModel):
    idea_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    name: Optional[str] = None
    value: Optional[float] = None
    type: Optional[str] = None
    recorded_at: Optional[datetime] = None

class IdeaMetricResponse(IdeaMetricBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
