import uuid

from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Usage(Base):
    """
    SQLAlchemy model representing resource usage by a User.
    """

    __tablename__ = "usages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resource_type = Column(String, nullable=False)

    # Legacy token counters (kept for analytics, no longer used for gating)
    used        = Column(Integer, default=0)
    limit_value = Column(Integer)

    # Pay-Per-Feature: flat-price feature purchases
    ppf_purchased = Column(Integer, default=0)  # total feature runs ever bought
    ppf_used      = Column(Integer, default=0)  # feature runs consumed

    # Credit system (primary billing gate)
    credits_used  = Column(Integer, default=0)   # credits spent this billing period
    credits_limit = Column(Integer, default=15)  # period allowance (15 Free, 90 Pro, 150 Premium)
    period_start  = Column(Date, nullable=True)  # when the current billing period started

    # Daily chat turn counter (Free and PAYG: 20 turns/day)
    chat_turns_today = Column(Integer, default=0)
    chat_turns_date  = Column(Date, nullable=True)  # date of last reset

    user = relationship("User", back_populates="usages")
