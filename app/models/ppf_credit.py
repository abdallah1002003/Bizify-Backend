import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PPFCredit(Base):
    """
    Tracks Pay-Per-Feature credit purchases.

    Each row records one purchase event (quantity of sections bought).
    The running balance is derived by summing all rows for the user and
    subtracting the sections already consumed (tracked via usages.ppf_used).
    """

    __tablename__ = "ppf_credits"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quantity       = Column(Integer, nullable=False)          # sections purchased
    amount_paid    = Column(Numeric(10, 2), nullable=False)   # total EGP paid
    currency       = Column(String, default="EGP")
    payment_method = Column(String, nullable=False)           # "paymob" | "paypal"
    payment_ref    = Column(String, nullable=True)            # order / capture ID
    status         = Column(String, default="pending")        # pending | succeeded
    created_at     = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ppf_credits")
