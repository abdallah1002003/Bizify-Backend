import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Payment(Base):
    """
    SQLAlchemy model representing a payment transaction.
    """

    __tablename__ = "payments"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    subscription_id = Column(UUID(as_uuid = True), ForeignKey("subscriptions.id"))
    payment_method_id = Column(UUID(as_uuid = True), ForeignKey("payment_methods.id"))
    amount = Column(Numeric(10, 2), nullable = False)
    currency = Column(String, default = "USD")
    # e.g., "succeeded", "failed"
    status = Column(String, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    user = relationship("User", back_populates = "payments")
    subscription = relationship("Subscription", back_populates = "payments")
    payment_method = relationship("PaymentMethod", back_populates = "payments")
