import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, JSON, Float, Integer
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import SubscriptionStatus

def utc_now():
    return datetime.now(timezone.utc)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    features_json = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)

    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(GUID, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)
    token_ref = Column(String, nullable=False)
    last4 = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", foreign_keys=[user_id], back_populates="payment_methods")
    payments = relationship("Payment", back_populates="payment_method")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(GUID, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    payment_method_id = Column(GUID, ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", foreign_keys=[user_id], back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
    payment_method = relationship("PaymentMethod", back_populates="payments")

class Usage(Base):
    __tablename__ = "usages"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String, nullable=False)
    used = Column(Integer, default=0)
    limit_value = Column(Integer, nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="usages")
