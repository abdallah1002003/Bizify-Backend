import uuid

from sqlalchemy import Boolean, Column, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Plan(Base):
    """
    SQLAlchemy model representing a subscription plan.
    """

    __tablename__ = "plans"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name = Column(String, nullable = False)
    price = Column(Numeric(10, 2), nullable = False)
    features_json = Column(JSON)
    is_active = Column(Boolean, default = True)

    subscriptions = relationship("Subscription", back_populates = "plan")
