from sqlalchemy import Column, String, Boolean, DateTime, Enum , Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user" 
    ENTREPRENEUR = "entrepreneur"
    MENTOR = "mentor"
    SUPPLIER = "supplier"
    MANUFACTURER = "manufacturer"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False) 
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)

    @property
    def is_locked(self) -> bool:
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    


    profile = relationship("UserProfile", back_populates="user", uselist=False)
    ideas = relationship("Idea", back_populates="owner")
    businesses = relationship("Business", back_populates="owner")
    subscriptions = relationship("Subscription", back_populates="user")
    payment_methods = relationship("PaymentMethod", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    usages = relationship("Usage", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    files = relationship("File", back_populates="owner")
    partner_profile = relationship("PartnerProfile", back_populates="user", uselist=False, foreign_keys="[PartnerProfile.user_id]")
    admin_logs = relationship("AdminActionLog", back_populates="admin")
    comparisons = relationship("IdeaComparison", back_populates="user")
    share_links = relationship("ShareLink", back_populates="creator")
    chat_sessions = relationship("ChatSession", back_populates="user")
    
