import uuid
from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer
from app.db.guid import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.core.crud_utils import _utc_now as utc_now

if TYPE_CHECKING:
    from app.models.users.user import User
    from app.models.ideation.idea import Idea

class IdeaComparison(Base):
    __tablename__ = "idea_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="idea_comparisons")
    items: Mapped[List["ComparisonItem"]] = relationship("ComparisonItem", back_populates="comparison", cascade="all, delete-orphan", order_by="ComparisonItem.rank_index")
    metrics: Mapped[List["ComparisonMetric"]] = relationship("ComparisonMetric", back_populates="comparison", cascade="all, delete-orphan")

class ComparisonItem(Base):
    __tablename__ = "comparison_items"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    comparison_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("idea_comparisons.id", ondelete="CASCADE"), nullable=False)
    idea_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False)
    rank_index: Mapped[int] = mapped_column(Integer, nullable=False)

    comparison: Mapped["IdeaComparison"] = relationship("IdeaComparison", back_populates="items")
    idea: Mapped["Idea"] = relationship("Idea", foreign_keys=[idea_id], back_populates="comparisons")

class ComparisonMetric(Base):
    __tablename__ = "comparison_metrics"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    comparison_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("idea_comparisons.id", ondelete="CASCADE"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    comparison: Mapped["IdeaComparison"] = relationship("IdeaComparison", back_populates="metrics")
