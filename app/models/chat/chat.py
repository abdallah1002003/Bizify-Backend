# ruff: noqa: F821
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.guid import GUID
from app.db.database import Base
from app.models.enums import ChatSessionType, ChatRole
from app.models.mixins import TimestampMixin, SoftDeleteMixin

class ChatSession(Base, TimestampMixin, SoftDeleteMixin):
    """Chat session for conversations with AI and business context."""
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True
    )
    idea_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=True
    )
    session_type: Mapped[ChatSessionType] = mapped_column(Enum(ChatSessionType), nullable=False)
    conversation_summary_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(  # type: ignore
        "User", foreign_keys=[user_id], back_populates="chat_sessions"
    )
    business: Mapped[Optional["Business"]] = relationship(  # type: ignore
        "Business", foreign_keys=[business_id], back_populates="chat_sessions"
    )
    idea: Mapped[Optional["Idea"]] = relationship(  # type: ignore
        "Idea", foreign_keys=[idea_id], back_populates="chat_sessions"
    )
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )

class ChatMessage(Base, TimestampMixin, SoftDeleteMixin):
    """Individual chat message in a conversation."""
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[ChatRole] = mapped_column(Enum(ChatRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
