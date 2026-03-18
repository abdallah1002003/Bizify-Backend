import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PaymentMethod(Base):
    """
    SQLAlchemy model representing a saved payment method for a User.
    """

    __tablename__ = "payment_methods"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    provider = Column(String, nullable = False)
    token_ref = Column(String, nullable = False)
    last4 = Column(String(4))
    is_default = Column(Boolean, default = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    user = relationship("User", back_populates = "payment_methods")
    payments = relationship("Payment", back_populates = "payment_method")
