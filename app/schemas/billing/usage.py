from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class UsageBase(BaseModel):
    user_id: UUID
    resource_type: str
    used: int
    limit_value: int

class UsageCreate(BaseModel):
    user_id: UUID
    resource_type: str = Field(..., max_length=255)
    used: int
    limit_value: int

class UsageUpdate(BaseModel):
    user_id: Optional[UUID] = None
    resource_type: Optional[str] = None
    used: Optional[int] = None
    limit_value: Optional[int] = None

class UsageResponse(UsageBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
