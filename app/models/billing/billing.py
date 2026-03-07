# ruff: noqa: F821
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from decimal import Decimal
<<<<<<< HEAD
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, JSON, Numeric, Integer, Index, UniqueConstraint
=======
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, JSON, Numeric, Integer, Index
>>>>>>> origin/main
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.guid import GUID
from app.core.encryption import EncryptedString
from app.db.database import Base
from app.models.enums import SubscriptionStatus, PaymentStatus
from config.settings import settings
from app.models.mixins import TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.users.user import User


class Plan(Base, TimestampMixin, SoftDeleteMixin):
    """Subscription plan definition."""
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    features_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True, index=True)
    billing_cycle: Mapped[str] = mapped_column(String, default="month", nullable=False)

    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="plan", cascade="all, delete-orphan"
    )

class Subscription(Base, TimestampMixin, SoftDeleteMixin):
    """User subscription model with plan and payment relationships."""
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String, unique=True, nullable=True, index=True
    )

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="subscriptions"
    )
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="subscription", cascade="all, delete-orphan"
    )

class PaymentMethod(Base, TimestampMixin, SoftDeleteMixin):
    """Payment method stored for a user with encryption."""
    __tablename__ = "payment_methods"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    token_ref: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    last4: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="payment_methods"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="payment_method"
    )

class Payment(Base, TimestampMixin, SoftDeleteMixin):
    """Payment transaction record with status tracking."""
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payment_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default=settings.DEFAULT_CURRENCY)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="payments"
    )
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="payments"
    )
    payment_method: Mapped[Optional["PaymentMethod"]] = relationship(
        "PaymentMethod", back_populates="payments"
    )

class Usage(Base, TimestampMixin, SoftDeleteMixin):
    """Resource usage tracking per user and resource type."""
    __tablename__ = "usages"
<<<<<<< HEAD
    ##Afnan - Added unique constraint for usages
    __table_args__ = (
        Index("ix_usages_user_id_resource_type", "user_id", "resource_type"),
        UniqueConstraint("user_id", "resource_type", name="uq_usage_user_resource_type"),
=======
    __table_args__ = (
        Index("ix_usages_user_id_resource_type", "user_id", "resource_type"),
>>>>>>> origin/main
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    used: Mapped[int] = mapped_column(Integer, default=0)
    limit_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="usages"
    )
