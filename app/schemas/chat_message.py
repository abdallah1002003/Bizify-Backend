import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.chat_message import MessageRole


class ChatMessageBase(BaseModel):
    """
    Base Pydantic model for Chat Message data.
    """
    
    session_id: uuid.UUID
    content: str

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class ChatMessageCreate(ChatMessageBase):
    """
    Pydantic model for creating a new Chat Message.
    """
    
    pass


class ChatMessageRead(ChatMessageBase):
    """
    Pydantic model for reading Chat Message data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
