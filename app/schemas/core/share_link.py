from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class ShareLinkBase(BaseModel):
    idea_id: UUID
    business_id: UUID
    created_by: UUID
    token: str
    is_public: Optional[bool] = None

class ShareLinkCreate(BaseModel):
    idea_id: UUID
    business_id: UUID
    created_by: UUID
    token: str = Field(..., max_length=255)
    is_public: Optional[bool] = None

class ShareLinkUpdate(BaseModel):
    idea_id: Optional[UUID] = None
    business_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    token: Optional[str] = None
    is_public: Optional[bool] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class ShareLinkResponse(ShareLinkBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
