# ruff: noqa: F821
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.guid import GUID
from app.db.database import Base
from app.models.enums import IdeaStatus, ExperimentStatus, MetricType
from app.models.mixins import TimestampMixin, SoftDeleteMixin

class Idea(Base, TimestampMixin, SoftDeleteMixin):
    """Business idea with versions, metrics, and experiments."""
    __tablename__ = "ideas"
    __table_args__ = (
        CheckConstraint('ai_score >= 0 AND ai_score <= 1', name='check_ai_score_range'),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("businesses.id", ondelete="SET NULL", use_alter=True, name="fk_ideas_business_id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[IdeaStatus] = mapped_column(Enum(IdeaStatus), default=IdeaStatus.DRAFT)
    ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    owner: Mapped["User"] = relationship(  # type: ignore
        "User", foreign_keys=[owner_id], back_populates="ideas"
    )
    business: Mapped[Optional["Business"]] = relationship(  # type: ignore
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
    chat_sessions: Mapped[List["ChatSession"]] = relationship(  # type: ignore
        "ChatSession", foreign_keys="ChatSession.idea_id", back_populates="idea",
        cascade="all, delete-orphan"
    )
    share_links: Mapped[List["ShareLink"]] = relationship(  # type: ignore
        "ShareLink", foreign_keys="ShareLink.idea_id", back_populates="idea",
        cascade="all, delete-orphan"
    )
    comparisons: Mapped[List["ComparisonItem"]] = relationship(  # type: ignore
        "ComparisonItem", back_populates="idea", cascade="all, delete-orphan"
    )
    accesses: Mapped[List["IdeaAccess"]] = relationship(
        "IdeaAccess", back_populates="idea", cascade="all, delete-orphan"
    )
    business_invites: Mapped[List["BusinessInviteIdea"]] = relationship(  # type: ignore
        "BusinessInviteIdea", back_populates="idea", cascade="all, delete-orphan"
    )

class IdeaVersion(Base, TimestampMixin, SoftDeleteMixin):
    """Version snapshot of an idea for tracking changes."""
    __tablename__ = "idea_versions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    idea: Mapped["Idea"] = relationship("Idea", back_populates="versions")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])  # type: ignore

class IdeaMetric(Base, TimestampMixin, SoftDeleteMixin):
    """Metric tracking for idea validation and analysis."""
    __tablename__ = "idea_metrics"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[MetricType] = mapped_column(
        Enum(MetricType), nullable=False, default=MetricType.CUSTOM
    )

    idea: Mapped["Idea"] = relationship("Idea", back_populates="metrics")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])  # type: ignore

class Experiment(Base, TimestampMixin, SoftDeleteMixin):
    """Experiment for testing idea hypotheses."""
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    hypothesis: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), nullable=False, default=ExperimentStatus.RUNNING
    )
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    idea: Mapped["Idea"] = relationship("Idea", back_populates="experiments")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])  # type: ignore

class IdeaAccess(Base, TimestampMixin, SoftDeleteMixin):
    """Access control permissions for ideas."""
    __tablename__ = "idea_accesses"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False
    )
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    can_experiment: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_job: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    idea: Mapped["Idea"] = relationship("Idea", back_populates="accesses")
    business: Mapped[Optional["Business"]] = relationship(  # type: ignore
        "Business", back_populates="idea_accesses"
    )
    user: Mapped["User"] = relationship(  # type: ignore
        "User", foreign_keys=[user_id], back_populates="idea_accesses"
    )
