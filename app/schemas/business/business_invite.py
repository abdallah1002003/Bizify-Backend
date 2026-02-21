from app.models.enums import InviteStatus
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic import EmailStr
from typing import Optional
from uuid import UUID

class BusinessInviteBase(BaseModel):
    business_id: UUID
    email: EmailStr
    token: str
    status: InviteStatus
    invited_by: UUID

class BusinessInviteCreate(BaseModel):
    business_id: UUID
    email: EmailStr
    token: str = Field(..., max_length=255)
    status: InviteStatus
    invited_by: UUID
    expires_at: Optional[datetime] = None

class BusinessInviteUpdate(BaseModel):
    business_id: Optional[UUID] = None
    email: Optional[EmailStr] = None
    token: Optional[str] = None
    status: Optional[InviteStatus] = None
    invited_by: Optional[UUID] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class BusinessInviteResponse(BusinessInviteBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
