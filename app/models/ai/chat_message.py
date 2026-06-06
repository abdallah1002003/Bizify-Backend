import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MessageRole(str, enum.Enum):
    """
    Enumeration of participant roles within a chat message.
    """
    
    USER = "USER"
    AI = "AI"


class ChatMessage(Base):
    """
    SQLAlchemy model representing a single message in a chat conversation.
    Stores the role (user/ai), content, and timestamp for sequencing.
    """
    
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    session_id = Column(UUID(as_uuid = True), ForeignKey("chat_sessions.id"), nullable = False)
    
    role = Column(
        Enum(MessageRole, values_callable = lambda x: [e.value for e in x]), 
        nullable = False
    )
    
    content = Column(Text, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    session = relationship("ChatSession", back_populates = "messages")
