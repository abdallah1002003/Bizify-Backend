import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ChatSessionBase(BaseModel):
    """
    Base Pydantic model for Chat Session data.
    """
    
    user_id: uuid.UUID
    business_id: Optional[uuid.UUID] = None
    idea_id: Optional[uuid.UUID] = None
    conversation_summary_json: Optional[Any] = None

    @field_validator("session_type", mode="before")
    @classmethod
    def validate_session_type(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


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
