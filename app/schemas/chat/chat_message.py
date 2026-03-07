from app.models.enums import ChatRole
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class ChatMessageBase(BaseModel):
    session_id: UUID
    role: ChatRole
    content: str

class ChatMessageCreate(BaseModel):
    session_id: UUID
    role: ChatRole
    content: str

class ChatMessageUpdate(BaseModel):
    session_id: Optional[UUID] = None
    role: Optional[ChatRole] = None
    content: Optional[str] = None
    created_at: Optional[datetime] = None

class ChatMessageResponse(ChatMessageBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
