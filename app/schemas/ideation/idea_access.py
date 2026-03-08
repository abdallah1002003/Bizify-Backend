from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class IdeaAccessBase(BaseModel):
    idea_id: UUID
    business_id: UUID
    user_id: UUID
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_experiment: Optional[bool] = None
    assigned_job: str

class IdeaAccessCreate(BaseModel):
    idea_id: UUID
    business_id: UUID
    user_id: UUID
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_experiment: Optional[bool] = None
    assigned_job: str

class IdeaAccessUpdate(BaseModel):
    idea_id: Optional[UUID] = None
    business_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_experiment: Optional[bool] = None
    assigned_job: Optional[str] = None
    created_at: Optional[datetime] = None

class IdeaAccessResponse(IdeaAccessBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
