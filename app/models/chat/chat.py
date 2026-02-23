import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Text, Enum, JSON
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import ChatSessionType, ChatRole
from app.core.crud_utils import _utc_now as utc_now

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)
    idea_id = Column(GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=True)
    session_type = Column(Enum(ChatSessionType), nullable=False)
    conversation_summary_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", foreign_keys=[user_id], back_populates="chat_sessions")
    business = relationship("Business", foreign_keys=[business_id], back_populates="chat_sessions")
    idea = relationship("Idea", foreign_keys=[idea_id], back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(ChatRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("ChatSession", back_populates="messages")
