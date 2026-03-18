import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class IdeaMetric(Base):
    """
    SQLAlchemy model representing a numerical metric for a Business Idea.
    """

    __tablename__ = "idea_metrics"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    idea_id = Column(UUID(as_uuid = True), ForeignKey("ideas.id"), nullable = False)
    created_by = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    name = Column(String, nullable = False)
    value = Column(Float, nullable = False)
    type = Column(String)
    recorded_at = Column(DateTime, default = datetime.utcnow)

    idea = relationship("Idea", back_populates = "metrics")
    creator = relationship("User")
