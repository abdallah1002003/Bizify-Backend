import uuid

from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComparisonMetric(Base):
    """
    SQLAlchemy model representing a metric used for Idea Comparison.
    """

    __tablename__ = "comparison_metrics"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    comparison_id = Column(
        UUID(as_uuid = True),
        ForeignKey("idea_comparisons.id"),
        nullable = False
    )
    metric_name = Column(String, nullable = False)
    value = Column(Float)

    comparison = relationship("IdeaComparison", back_populates = "metrics")
