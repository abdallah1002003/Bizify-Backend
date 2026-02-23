import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import UserRole
from app.core.crud_utils import _utc_now as utc_now

class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships mapped to other entities (will resolve dynamically in SQLAlchemy)
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    ideas = relationship("Idea", foreign_keys="Idea.owner_id", back_populates="owner", cascade="all, delete-orphan", lazy="select")
    businesses = relationship("Business", foreign_keys="Business.owner_id", back_populates="owner", cascade="all, delete-orphan", lazy="select")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan", lazy="select")
    payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan", lazy="select")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan", lazy="select")
    usages = relationship("Usage", back_populates="user", cascade="all, delete-orphan", lazy="select")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan", lazy="select")
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan", lazy="select")
    partner_profiles = relationship("PartnerProfile", foreign_keys="PartnerProfile.user_id", back_populates="user", cascade="all, delete-orphan", lazy="select")
    admin_actions = relationship("AdminActionLog", foreign_keys="AdminActionLog.admin_id", back_populates="admin", cascade="all, delete-orphan", lazy="select")
    idea_comparisons = relationship("IdeaComparison", back_populates="user", cascade="all, delete-orphan", lazy="select")
    share_links = relationship("ShareLink", foreign_keys="ShareLink.created_by", back_populates="creator", cascade="all, delete-orphan", lazy="select")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan", lazy="select")
    business_invites_sent = relationship("BusinessInvite", foreign_keys="BusinessInvite.invited_by", back_populates="inviter", cascade="all, delete-orphan", lazy="select")
    idea_accesses = relationship("IdeaAccess", back_populates="user", cascade="all, delete-orphan", lazy="select")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    bio = Column(Text, nullable=True)
    skills_json = Column(JSON, nullable=True)
    interests_json = Column(JSON, nullable=True)
    preferences_json = Column(JSON, nullable=True)
    risk_profile_json = Column(JSON, nullable=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="profile")


class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    admin_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String, nullable=False)
    target_entity = Column(String, nullable=False)
    target_id = Column(GUID, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    admin = relationship("User", back_populates="admin_actions")


class RefreshToken(Base):
    """Stores refresh tokens in database for revocation and validation."""
    __tablename__ = "refresh_tokens"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)  # JWT ID for unique identification
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", foreign_keys=[user_id])
