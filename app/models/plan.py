from sqlalchemy import Column, String, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from sqlalchemy import JSON

class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    features_json = Column(JSON)
    is_active = Column(Boolean, default=True)

    subscriptions = relationship("Subscription", back_populates="plan")
