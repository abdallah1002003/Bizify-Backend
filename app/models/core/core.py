import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.core.crud_utils import _utc_now as utc_now  # type: ignore

class File(Base):
    __tablename__ = "files"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    owner_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=utc_now)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="files")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")

class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id = Column(GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=True)
    business_id = Column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)
    created_by = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    is_public = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    idea = relationship("Idea", foreign_keys=[idea_id], back_populates="share_links")
    business = relationship("Business", foreign_keys=[business_id], back_populates="share_links")
    creator = relationship("User", foreign_keys=[created_by], back_populates="share_links")

class EmailMessage(Base):
    """Database-backed queue for outgoing emails."""
    __tablename__ = "email_messages"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    to_email = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    html_body = Column(Text, nullable=False)
    
    # Statuses: PENDING, SENT, FAILED, RETRYING
    status = Column(String, default="PENDING", index=True, nullable=False)
    
    retries = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
