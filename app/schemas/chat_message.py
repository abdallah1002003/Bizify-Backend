from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.models.chat_message import MessageRole

class ChatMessageBase(BaseModel):
    session_id: UUID
    role: MessageRole
    content: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageRead(ChatMessageBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
