import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SessionType(str, enum.Enum):
    """
    Enumeration of context-specific chat session types.
    """
    
    IDEA_CHAT = "IDEA_CHAT"
    BUSINESS_CHAT = "BUSINESS_CHAT"
    STAGE_CHAT = "STAGE_CHAT"
    GENERAL = "GENERAL"


class ChatSession(Base):
    """
    SQLAlchemy model representing a persistent conversation thread with the AI.
    Links to users and optionally to specific ideas or businesses for context.
    """
    
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    business_id = Column(UUID(as_uuid = True), ForeignKey("businesses.id"))
    idea_id = Column(UUID(as_uuid = True), ForeignKey("ideas.id"))
    
    session_type = Column(
        Enum(SessionType, values_callable = lambda x: [e.value for e in x]), 
        nullable = False
    )
    
    conversation_summary_json = Column(JSON)
    created_at = Column(DateTime, default = datetime.utcnow)

    user = relationship("User", back_populates = "chat_sessions")
    business = relationship("Business", back_populates = "chat_sessions")
    idea = relationship("Idea", back_populates = "chat_sessions")
    messages = relationship("ChatMessage", back_populates = "session")
