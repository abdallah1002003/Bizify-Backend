from sqlalchemy import Column, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class SessionType(str, enum.Enum):
    IDEA_CHAT = "idea_chat"
    BUSINESS_CHAT = "business_chat"
    STAGE_CHAT = "stage_chat"
    GENERAL = "general"

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    idea_id = Column(UUID(as_uuid=True), ForeignKey("ideas.id"))
    session_type = Column(Enum(SessionType), nullable=False)
    conversation_summary_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    business = relationship("Business", back_populates="chat_sessions")
    idea = relationship("Idea", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")
