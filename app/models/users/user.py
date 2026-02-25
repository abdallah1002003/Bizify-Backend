# ruff: noqa: F821
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.guid import GUID
from app.db.database import Base
from app.models.enums import UserRole
from app.models.mixins import TimestampMixin, SoftDeleteMixin

class User(Base, TimestampMixin, SoftDeleteMixin):
    """User account model with profile and relationships.
    
    Represents a user account in the system with authentication, 
    billing, and content management relationships.
    
    Attributes:
        id: Unique identifier (GUID)
        name: User's display name
        email: User's email address (unique, indexed)
        password_hash: Hashed password for authentication
        role: User role (UserRole enum)
        is_active: Account activation status
        is_verified: Email verification status
        stripe_customer_id: External Stripe customer ID for billing
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String, unique=True, nullable=True, index=True
    )

    # Relationships mapped to other entities (will resolve dynamically in SQLAlchemy)
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    ideas: Mapped[List["Idea"]] = relationship(
        "Idea", foreign_keys="Idea.owner_id", back_populates="owner",
        cascade="all, delete-orphan", lazy="select"
    )
    businesses: Mapped[List["Business"]] = relationship(
        "Business", foreign_keys="Business.owner_id", back_populates="owner",
        cascade="all, delete-orphan", lazy="select"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    payment_methods: Mapped[List["PaymentMethod"]] = relationship(
        "PaymentMethod", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    usages: Mapped[List["Usage"]] = relationship(
        "Usage", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    files: Mapped[List["File"]] = relationship(
        "File", back_populates="owner", cascade="all, delete-orphan", lazy="select"
    )
    partner_profiles: Mapped[List["PartnerProfile"]] = relationship(
        "PartnerProfile", foreign_keys="PartnerProfile.user_id", back_populates="user",
        cascade="all, delete-orphan", lazy="select"
    )
    admin_actions: Mapped[List["AdminActionLog"]] = relationship(
        "AdminActionLog", foreign_keys="AdminActionLog.admin_id", back_populates="admin",
        cascade="all, delete-orphan", lazy="select"
    )
    idea_comparisons: Mapped[List["IdeaComparison"]] = relationship(
        "IdeaComparison", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    share_links: Mapped[List["ShareLink"]] = relationship(
        "ShareLink", foreign_keys="ShareLink.created_by", back_populates="creator",
        cascade="all, delete-orphan", lazy="select"
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    business_invites_sent: Mapped[List["BusinessInvite"]] = relationship(
        "BusinessInvite", foreign_keys="BusinessInvite.invited_by", back_populates="inviter",
        cascade="all, delete-orphan", lazy="select"
    )
    idea_accesses: Mapped[List["IdeaAccess"]] = relationship(
        "IdeaAccess", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )

class UserProfile(Base, TimestampMixin, SoftDeleteMixin):
    """User profile for storing extended user information.
    
    Extends the User model with optional profile data including
    bio, skills, interests, preferences, and onboarding status.
    
    Attributes:
        id: Unique identifier (GUID)
        user_id: Foreign key to User (one-to-one relationship)
        bio: User biography text (optional)
        skills_json: JSON array of user skills
        interests_json: JSON array of user interests
        preferences_json: User preferences stored as JSON
        risk_profile_json: Risk profile assessment stored as JSON
        onboarding_completed: Flag indicating if onboarding is complete
    """
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    interests_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    preferences_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    risk_profile_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class AdminActionLog(Base, TimestampMixin, SoftDeleteMixin):
    """Audit log for administrative actions.
    
    Tracks administrative actions performed on the system for
    security auditing and accountability purposes.
    
    Attributes:
        id: Unique identifier (GUID)
        admin_id: Foreign key to User (admin performing action)
        action_type: Type of action (string descriptor)
        target_entity: Entity type being acted upon
        target_id: ID of the entity being acted upon
    """
    __tablename__ = "admin_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    target_entity: Mapped[str] = mapped_column(String, nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False)

    admin: Mapped[Optional["User"]] = relationship("User", back_populates="admin_actions")


class RefreshToken(Base, TimestampMixin, SoftDeleteMixin):
    """Refresh token store for token revocation and validation.
    
    Stores issued refresh tokens in the database for:
    1. Token validation on refresh requests
    2. Token revocation (logout)
    3. Security auditing and rate limiting
    
    Attributes:
        id: Unique identifier (GUID)
        user_id: Foreign key to User
        jti: JWT ID for unique token identification
        expires_at: Token expiration timestamp (UTC)
        revoked: Flag indicating if token has been revoked
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class PasswordResetToken(Base, TimestampMixin, SoftDeleteMixin):
    """Stores password reset tokens for one-time use tracking."""
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class EmailVerificationToken(Base, TimestampMixin, SoftDeleteMixin):
    """Stores email verification tokens for one-time account confirmation."""
    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

