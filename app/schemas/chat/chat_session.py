from app.models.enums import ChatSessionType
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class ChatSessionBase(BaseModel):
    user_id: UUID
    business_id: Optional[UUID] = None
    idea_id: Optional[UUID] = None
    session_type: ChatSessionType
    conversation_summary_json: Optional[dict] = None

class ChatSessionCreate(BaseModel):
    user_id: UUID
    business_id: Optional[UUID] = None
    idea_id: Optional[UUID] = None
    session_type: ChatSessionType
    conversation_summary_json: Optional[dict] = None

class ChatSessionUpdate(BaseModel):
    user_id: Optional[UUID] = None
    business_id: Optional[UUID] = None
    idea_id: Optional[UUID] = None
    session_type: Optional[ChatSessionType] = None
    conversation_summary_json: Optional[dict] = None
    created_at: Optional[datetime] = None

class ChatSessionResponse(ChatSessionBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
