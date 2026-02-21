from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class IdeaComparisonBase(BaseModel):
    user_id: UUID
    name: str

class IdeaComparisonCreate(BaseModel):
    user_id: UUID
    name: str = Field(..., max_length=255)

class IdeaComparisonUpdate(BaseModel):
    user_id: Optional[UUID] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = None

class IdeaComparisonResponse(IdeaComparisonBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
