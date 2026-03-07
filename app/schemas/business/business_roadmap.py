from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class BusinessRoadmapBase(BaseModel):
    business_id: UUID
    completion_percentage: float

class BusinessRoadmapCreate(BaseModel):
    business_id: UUID
    completion_percentage: float

class BusinessRoadmapUpdate(BaseModel):
    business_id: Optional[UUID] = None
    completion_percentage: Optional[float] = None
    created_at: Optional[datetime] = None

class BusinessRoadmapResponse(BusinessRoadmapBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
