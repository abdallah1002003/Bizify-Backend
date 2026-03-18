import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationStatus(str, enum.Enum):
    """
    Status of the notification delivery/read state.
    """
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"
    ARCHIVED = "archived"


class DeliveryStatus(str, enum.Enum):
    """
    Status of the secondary delivery (Email/SMS).
    """
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Notification(Base):
    """
    SQLAlchemy model representing a system notification for a user.
    """
    
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(
        UUID(as_uuid = True), 
        ForeignKey("users.id", ondelete = "CASCADE"), 
        nullable = False
    )
    
    title = Column(String, nullable = False)
    content = Column(Text, nullable = True)
    message = Column(Text, nullable = False) # Required by DB schema
    type = Column(String, nullable = False)  # e.g., "TEAM_JOIN", "SYSTEM", "BILLING"
    
    status = Column(
        Enum(NotificationStatus), 
        default = NotificationStatus.UNREAD, 
        nullable = False
    )
    
    delivery_status = Column(
        Enum(DeliveryStatus), 
        default = DeliveryStatus.PENDING, 
        nullable = False
    )
    
    retry_count = Column(Integer, default = 0)
    expires_at = Column(DateTime, nullable = True)
    created_at = Column(DateTime, default = datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates = "notifications")

    # performance: Composite index for fast filtering of active notifications per user
    __table_args__ = (
        Index("ix_notifications_user_status_expiry", "user_id", "status", "expires_at"),
    )
