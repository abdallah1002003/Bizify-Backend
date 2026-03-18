import uuid

from sqlalchemy import Boolean, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationSetting(Base):
    """
    SQLAlchemy model representing user-specific notification preferences.
    """
    
    __tablename__ = "notification_settings"

    # Primary key is the user_id to ensure 1-to-1 relationship
    user_id = Column(
        UUID(as_uuid = True), 
        ForeignKey("users.id", ondelete = "CASCADE"), 
        primary_key = True
    )
    
    is_enabled = Column(Boolean, default = True)  # Global toggle
    
    # Channel toggles
    email_enabled = Column(Boolean, default = True)
    sms_enabled = Column(Boolean, default = False)
    push_enabled = Column(Boolean, default = True)
    
    # Category toggles
    marketing_enabled = Column(Boolean, default = False)
    team_updates_enabled = Column(Boolean, default = True)
    billing_alerts_enabled = Column(Boolean, default = True)

    # Relationships
    user = relationship("User", back_populates = "notification_settings")
