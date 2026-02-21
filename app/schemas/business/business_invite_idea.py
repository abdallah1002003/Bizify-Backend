from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class BusinessInviteIdeaBase(BaseModel):
    invite_id: UUID
    idea_id: UUID

class BusinessInviteIdeaCreate(BaseModel):
    invite_id: UUID
    idea_id: UUID

class BusinessInviteIdeaUpdate(BaseModel):
    invite_id: Optional[UUID] = None
    idea_id: Optional[UUID] = None

class BusinessInviteIdeaResponse(BusinessInviteIdeaBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
