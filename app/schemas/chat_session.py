import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.chat_session import SessionType


class ChatSessionBase(BaseModel):
    """
    Base Pydantic model for Chat Session data.
    """
    
    user_id: uuid.UUID
    business_id: Optional[uuid.UUID] = None
    idea_id: Optional[uuid.UUID] = None
    session_type: SessionType
    conversation_summary_json: Optional[Any] = None


class ChatSessionCreate(ChatSessionBase):
    """
    Pydantic model for creating a new Chat Session.
    """
    
    pass


class ChatSessionRead(ChatSessionBase):
    """
    Pydantic model for reading Chat Session data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
