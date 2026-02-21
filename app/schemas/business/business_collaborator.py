from app.models.enums import CollaboratorRole
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class BusinessCollaboratorBase(BaseModel):
    business_id: UUID
    user_id: UUID
    role: CollaboratorRole

class BusinessCollaboratorCreate(BaseModel):
    business_id: UUID
    user_id: UUID
    role: CollaboratorRole

class BusinessCollaboratorUpdate(BaseModel):
    business_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    role: Optional[CollaboratorRole] = None
    added_at: Optional[datetime] = None

class BusinessCollaboratorResponse(BusinessCollaboratorBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
