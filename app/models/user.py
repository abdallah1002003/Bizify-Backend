import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """
    Enumeration of user roles within the system.
    """

    ADMIN = "admin"
    USER = "user" 
    ENTREPRENEUR = "entrepreneur"
    MENTOR = "mentor"
    SUPPLIER = "supplier"
    MANUFACTURER = "manufacturer"


class User(Base):
    """
    SQLAlchemy model representing a system User.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    email = Column(String, unique = True, index = True, nullable = False)
    password_hash = Column(String, nullable = False)
    full_name = Column(String, nullable = True)
    
    role = Column(
        Enum(UserRole, values_callable = lambda x: [e.value for e in x]), 
        default = UserRole.USER, 
        nullable = False
    ) 
    
    is_active = Column(Boolean, default = True)
    is_verified = Column(Boolean, default = False)
    
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)
    
    failed_login_attempts = Column(Integer, default = 0)
    locked_until = Column(DateTime, nullable = True)
    last_activity = Column(DateTime, default = datetime.utcnow)
    revoked_at = Column(DateTime, nullable = True)
    last_password_change = Column(DateTime, nullable = True)

    @property
    def is_locked(self) -> bool:
        """
        Property to check if the user account is currently locked.
        """
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
            
        return False

    profile = relationship("UserProfile", back_populates = "user", uselist = False)
    ideas = relationship("Idea", back_populates = "owner")
    businesses = relationship("Business", back_populates = "owner")
    subscriptions = relationship("Subscription", back_populates = "user")
    payment_methods = relationship("PaymentMethod", back_populates = "user")
    payments = relationship("Payment", back_populates = "user")
    usages = relationship("Usage", back_populates = "user")
    notifications = relationship("Notification", back_populates = "user")
    notification_settings = relationship("NotificationSetting", back_populates = "user", uselist = False)
    privacy_settings = relationship("PrivacySetting", back_populates = "user", uselist = False)
    files = relationship("File", back_populates = "owner")
    
    partner_profile = relationship(
        "PartnerProfile", 
        back_populates = "user", 
        uselist = False, 
        foreign_keys = "[PartnerProfile.user_id]"
    )
    
    admin_logs = relationship("AdminActionLog", back_populates = "admin")
    comparisons = relationship("IdeaComparison", back_populates = "user")
    share_links = relationship("ShareLink", back_populates = "creator")
    chat_sessions = relationship("ChatSession", back_populates = "user")
    verification_codes = relationship("AccountVerification", back_populates = "user")
