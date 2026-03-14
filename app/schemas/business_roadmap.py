from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class BusinessRoadmapBase(BaseModel):
    business_id: UUID
    completion_percentage: Optional[float] = 0.0

class BusinessRoadmapCreate(BusinessRoadmapBase):
    pass

class BusinessRoadmapRead(BusinessRoadmapBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
