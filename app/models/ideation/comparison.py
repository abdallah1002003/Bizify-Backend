import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.core.crud_utils import _utc_now as utc_now

class IdeaComparison(Base):
    __tablename__ = "idea_comparisons"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", foreign_keys=[user_id], back_populates="idea_comparisons")
    items = relationship("ComparisonItem", back_populates="comparison", cascade="all, delete-orphan", order_by="ComparisonItem.rank_index")
    metrics = relationship("ComparisonMetric", back_populates="comparison", cascade="all, delete-orphan")

class ComparisonItem(Base):
    __tablename__ = "comparison_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    comparison_id = Column(GUID, ForeignKey("idea_comparisons.id", ondelete="CASCADE"), nullable=False)
    idea_id = Column(GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False)
    rank_index = Column(Integer, nullable=False)

    comparison = relationship("IdeaComparison", back_populates="items")
    idea = relationship("Idea", foreign_keys=[idea_id], back_populates="comparisons")

class ComparisonMetric(Base):
    __tablename__ = "comparison_metrics"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    comparison_id = Column(GUID, ForeignKey("idea_comparisons.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)

    comparison = relationship("IdeaComparison", back_populates="metrics")
