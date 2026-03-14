from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class ComparisonMetric(Base):
    __tablename__ = "comparison_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comparison_id = Column(UUID(as_uuid=True), ForeignKey("idea_comparisons.id"), nullable=False)
    metric_name = Column(String, nullable=False)
    value = Column(Float)

    comparison = relationship("IdeaComparison", back_populates="metrics")
