from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class ComparisonItemBase(BaseModel):
    comparison_id: UUID
    idea_id: UUID
    rank_index: int

class ComparisonItemCreate(BaseModel):
    comparison_id: UUID
    idea_id: UUID
    rank_index: int

class ComparisonItemUpdate(BaseModel):
    comparison_id: Optional[UUID] = None
    idea_id: Optional[UUID] = None
    rank_index: Optional[int] = None

class ComparisonItemResponse(ComparisonItemBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
