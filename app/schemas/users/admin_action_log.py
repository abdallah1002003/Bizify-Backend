from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class AdminActionLogBase(BaseModel):
    admin_id: UUID
    action_type: str
    target_entity: str
    target_id: Optional[UUID] = None

class AdminActionLogCreate(BaseModel):
    admin_id: UUID
    action_type: str = Field(..., max_length=255)
    target_entity: str = Field(..., max_length=255)
    target_id: Optional[UUID] = None

class AdminActionLogUpdate(BaseModel):
    admin_id: Optional[UUID] = None
    action_type: Optional[str] = None
    target_entity: Optional[str] = None
    target_id: Optional[UUID] = None
    created_at: Optional[datetime] = None

class AdminActionLogResponse(AdminActionLogBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
