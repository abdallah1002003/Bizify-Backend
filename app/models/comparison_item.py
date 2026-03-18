import uuid

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComparisonItem(Base):
    """
    SQLAlchemy model representing an item within an Idea Comparison.
    """

    __tablename__ = "comparison_items"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    comparison_id = Column(
        UUID(as_uuid = True),
        ForeignKey("idea_comparisons.id"),
        nullable = False
    )
    idea_id = Column(UUID(as_uuid = True), ForeignKey("ideas.id"), nullable = False)
    rank_index = Column(Integer)

    comparison = relationship("IdeaComparison", back_populates = "items")
    idea = relationship("Idea", back_populates = "comparison_items")
