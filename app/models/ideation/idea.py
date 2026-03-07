# ruff: noqa: F821
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
<<<<<<< HEAD
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Float, CheckConstraint, Index, UniqueConstraint
=======
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Float, CheckConstraint, Index
>>>>>>> origin/main
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.guid import GUID
from app.db.database import Base
from app.models.enums import IdeaStatus, ExperimentStatus, MetricType
from app.models.mixins import TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.users.user import User
    from app.models.business.business import Business, BusinessInviteIdea
    from app.models.chat.chat_session import ChatSession
    from app.models.core.share_link import ShareLink
    from app.models.ideation.comparison import ComparisonItem

class Idea(Base, TimestampMixin, SoftDeleteMixin):
    """Business idea with versions, metrics, and experiments."""
    __tablename__ = "ideas"
    __table_args__ = (
        CheckConstraint('ai_score >= 0 AND ai_score <= 1', name='check_ai_score_range'),
        Index("ix_ideas_owner_id_created_at", "owner_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[IdeaStatus] = mapped_column(Enum(IdeaStatus), default=IdeaStatus.DRAFT)
    ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    owner: Mapped["User"] = relationship(
        "User", foreign_keys=[owner_id], back_populates="ideas"
    )
    business: Mapped[Optional["Business"]] = relationship(
        "Business", foreign_keys=[business_id], back_populates="idea_backref"
    )
    versions: Mapped[List["IdeaVersion"]] = relationship(
        "IdeaVersion", back_populates="idea", cascade="all, delete-orphan"
    )
    metrics: Mapped[List["IdeaMetric"]] = relationship(
        "IdeaMetric", back_populates="idea", cascade="all, delete-orphan"
    )
    experiments: Mapped[List["Experiment"]] = relationship(
        "Experiment", back_populates="idea", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession", foreign_keys="ChatSession.idea_id", back_populates="idea",
        cascade="all, delete-orphan"
    )
    share_links: Mapped[List["ShareLink"]] = relationship(
        "ShareLink", foreign_keys="ShareLink.idea_id", back_populates="idea",
        cascade="all, delete-orphan"
    )
    comparisons: Mapped[List["ComparisonItem"]] = relationship(
        "ComparisonItem", back_populates="idea", cascade="all, delete-orphan"
    )
    accesses: Mapped[List["IdeaAccess"]] = relationship(
        "IdeaAccess", back_populates="idea", cascade="all, delete-orphan"
    )
    business_invites: Mapped[List["BusinessInviteIdea"]] = relationship(
        "BusinessInviteIdea", back_populates="idea", cascade="all, delete-orphan"
    )

class IdeaVersion(Base, TimestampMixin, SoftDeleteMixin):
    """Version snapshot of an idea for tracking changes."""
    __tablename__ = "idea_versions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    idea: Mapped["Idea"] = relationship("Idea", back_populates="versions")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])

class IdeaMetric(Base, TimestampMixin, SoftDeleteMixin):
    """Metric tracking for idea validation and analysis."""
    __tablename__ = "idea_metrics"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[MetricType] = mapped_column(
        Enum(MetricType), nullable=False, default=MetricType.CUSTOM
    )

    idea: Mapped["Idea"] = relationship("Idea", back_populates="metrics")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])

class Experiment(Base, TimestampMixin, SoftDeleteMixin):
    """Experiment for testing idea hypotheses."""
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    hypothesis: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), nullable=False, default=ExperimentStatus.RUNNING
    )
    result_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    idea: Mapped["Idea"] = relationship("Idea", back_populates="experiments")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])

class IdeaAccess(Base, TimestampMixin, SoftDeleteMixin):
    """Access control permissions for ideas."""
    __tablename__ = "idea_accesses"
<<<<<<< HEAD
    ##Afnan - Added unique constraint for idea_accesses (merged with index)
    __table_args__ = (
        Index("ix_idea_accesses_idea_id_user_id", "idea_id", "user_id"),
        UniqueConstraint("idea_id", "user_id", name="uq_idea_access_idea_user"),
=======
    __table_args__ = (
        Index("ix_idea_accesses_idea_id_user_id", "idea_id", "user_id"),
>>>>>>> origin/main
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    can_experiment: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_job: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    idea: Mapped["Idea"] = relationship("Idea", back_populates="accesses")
    business: Mapped[Optional["Business"]] = relationship(
        "Business", back_populates="idea_accesses"
    )
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="idea_accesses"
    )
