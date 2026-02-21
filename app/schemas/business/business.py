from app.models.enums import BusinessStage
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class BusinessBase(BaseModel):
    idea_id: Optional[UUID] = None
    owner_id: UUID
    stage: BusinessStage
    context_json: Optional[dict] = None
    is_archived: Optional[bool] = None

class BusinessCreate(BaseModel):
    idea_id: Optional[UUID] = None
    owner_id: UUID
    stage: BusinessStage
    context_json: Optional[dict] = None
    is_archived: Optional[bool] = None

class BusinessUpdate(BaseModel):
    idea_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    stage: Optional[BusinessStage] = None
    context_json: Optional[dict] = None
    is_archived: Optional[bool] = None
    archived_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BusinessResponse(BusinessBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
