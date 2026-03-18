import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BusinessRoadmapBase(BaseModel):
    """
    Base Pydantic model for Business Roadmap data.
    """
    
    business_id: uuid.UUID
    completion_percentage: Optional[float] = 0.0


class BusinessRoadmapCreate(BusinessRoadmapBase):
    """
    Pydantic model for creating a Business Roadmap.
    """
    
    pass


class BusinessRoadmapRead(BusinessRoadmapBase):
    """
    Pydantic model for reading Business Roadmap data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
