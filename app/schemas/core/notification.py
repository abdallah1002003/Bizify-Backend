from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class NotificationBase(BaseModel):
    user_id: UUID
    title: str
    message: str
    is_read: Optional[bool] = None

class NotificationCreate(BaseModel):
    user_id: UUID
    title: str = Field(..., max_length=255)
    message: str
    is_read: Optional[bool] = None

class NotificationUpdate(BaseModel):
    user_id: Optional[UUID] = None
    title: Optional[str] = None
    message: Optional[str] = None
    is_read: Optional[bool] = None
    created_at: Optional[datetime] = None

class NotificationResponse(NotificationBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
