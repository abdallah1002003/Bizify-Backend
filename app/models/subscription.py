import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SubscriptionStatus(str, enum.Enum):
    """
    Enumeration of subscription statuses.
    """

    ACTIVE = "ACTIVE"
    CANCELED = "CANCELED"


class Subscription(Base):
    """
    SQLAlchemy model representing a User's subscription to a Plan.
    """

    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    plan_id = Column(UUID(as_uuid = True), ForeignKey("plans.id"), nullable = False)
    status = Column(
        Enum(SubscriptionStatus, values_callable = lambda x: [e.value for e in x]),
        default = SubscriptionStatus.ACTIVE
    )
    start_date = Column(DateTime, default = datetime.utcnow)
    end_date = Column(DateTime)
    # PayPal billing agreement / subscription reference
    paypal_subscription_id = Column(String, nullable = True, index = True)

    user = relationship("User", back_populates = "subscriptions")
    plan = relationship("Plan", back_populates = "subscriptions")
    payments = relationship("Payment", back_populates = "subscription")
