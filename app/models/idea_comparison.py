import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class IdeaComparison(Base):
    """
    SQLAlchemy model representing a collection of ideas being compared.
    """

    __tablename__ = "idea_comparisons"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    name = Column(String, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    user = relationship("User", back_populates = "comparisons")
    items = relationship("ComparisonItem", back_populates = "comparison")
    metrics = relationship("ComparisonMetric", back_populates = "comparison")
