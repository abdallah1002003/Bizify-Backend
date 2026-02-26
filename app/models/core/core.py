import uuid
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer
from app.db.guid import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.core.crud_utils import _utc_now as utc_now

if TYPE_CHECKING:
    from app.models.users.user import User
    from app.models.ideation.idea import Idea
    from app.models.business.business import Business

class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id], back_populates="files")

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="notifications")

class ShareLink(Base):
    __tablename__ = "share_links"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=True, index=True
    )
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    idea: Mapped[Optional["Idea"]] = relationship("Idea", foreign_keys=[idea_id], back_populates="share_links")
    business: Mapped[Optional["Business"]] = relationship("Business", foreign_keys=[business_id], back_populates="share_links")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by], back_populates="share_links")

class EmailMessage(Base):
    """Database-backed queue for outgoing emails."""
    __tablename__ = "email_messages"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    to_email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    html_body: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Statuses: PENDING, SENT, FAILED, RETRYING
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True, nullable=False)
    
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
