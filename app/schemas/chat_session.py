from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from app.models.chat_session import SessionType

class ChatSessionBase(BaseModel):
    user_id: UUID
    business_id: Optional[UUID] = None
    idea_id: Optional[UUID] = None
    session_type: SessionType
    conversation_summary_json: Optional[Any] = None

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionRead(ChatSessionBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
