from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from app.models.business import BusinessStage

class BusinessBase(BaseModel):
    stage: Optional[BusinessStage] = BusinessStage.EARLY
    context_json: Optional[Any] = None
    is_archived: Optional[bool] = False

class BusinessCreate(BusinessBase):
    idea_id: Optional[UUID] = None
    owner_id: UUID

class BusinessUpdate(BaseModel):
    stage: Optional[BusinessStage] = None
    context_json: Optional[Any] = None
    is_archived: Optional[bool] = None

class BusinessRead(BusinessBase):
    id: UUID
    idea_id: Optional[UUID] = None
    owner_id: UUID
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
