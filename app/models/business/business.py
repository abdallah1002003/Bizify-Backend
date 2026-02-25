import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.guid import GUID
from app.db.database import Base
from app.models.enums import BusinessStage, CollaboratorRole, InviteStatus, StageType, RoadmapStageStatus
from app.core.crud_utils import _utc_now as utc_now
from app.models.mixins import TimestampMixin, SoftDeleteMixin

class Business(Base, TimestampMixin, SoftDeleteMixin):
    """Business entity created from an idea with collaborators and roadmap."""
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[BusinessStage] = mapped_column(Enum(BusinessStage), default=BusinessStage.EARLY)
    context_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    idea_backref: Mapped[Optional["Idea"]] = relationship(
        "Idea", foreign_keys="[Idea.business_id]", back_populates="business"
    )
    owner: Mapped["User"] = relationship(
        "User", foreign_keys=[owner_id], back_populates="businesses"
    )
    collaborators: Mapped[List["BusinessCollaborator"]] = relationship(
        "BusinessCollaborator", back_populates="business", cascade="all, delete-orphan"
    )
    invites: Mapped[List["BusinessInvite"]] = relationship(
        "BusinessInvite", back_populates="business", cascade="all, delete-orphan"
    )
    roadmap: Mapped[Optional["BusinessRoadmap"]] = relationship(
        "BusinessRoadmap", back_populates="business", uselist=False, cascade="all, delete-orphan"
    )
    partner_requests: Mapped[List["PartnerRequest"]] = relationship(
        "PartnerRequest", back_populates="business", cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["Embedding"]] = relationship(
        "Embedding", back_populates="business", cascade="all, delete-orphan"
    )
    idea_accesses: Mapped[List["IdeaAccess"]] = relationship(
        "IdeaAccess", back_populates="business", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession", foreign_keys="ChatSession.business_id", back_populates="business",
        cascade="all, delete-orphan"
    )
    share_links: Mapped[List["ShareLink"]] = relationship(
        "ShareLink", foreign_keys="ShareLink.business_id", back_populates="business",
        cascade="all, delete-orphan"
    )

class BusinessCollaborator(Base, TimestampMixin, SoftDeleteMixin):
    """Collaborator role assignment for business."""
    __tablename__ = "business_collaborators"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[CollaboratorRole] = mapped_column(Enum(CollaboratorRole), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    business: Mapped["Business"] = relationship("Business", back_populates="collaborators")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

class BusinessInvite(Base, TimestampMixin, SoftDeleteMixin):
    """Invitation to join a business with token tracking."""
    __tablename__ = "business_invites"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    status: Mapped[InviteStatus] = mapped_column(Enum(InviteStatus), default=InviteStatus.PENDING)
    invited_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="invites")
    inviter: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[invited_by], back_populates="business_invites_sent"
    )
    ideas_invited_for: Mapped[List["BusinessInviteIdea"]] = relationship(
        "BusinessInviteIdea", back_populates="invite", cascade="all, delete-orphan"
    )

class BusinessInviteIdea(Base, TimestampMixin, SoftDeleteMixin):
    """Junction table for ideas included in an invite."""
    __tablename__ = "business_invite_ideas"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    invite_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("business_invites.id", ondelete="CASCADE"), nullable=False
    )
    idea_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False
    )

    invite: Mapped["BusinessInvite"] = relationship(
        "BusinessInvite", back_populates="ideas_invited_for"
    )
    idea: Mapped["Idea"] = relationship("Idea", back_populates="business_invites")


class BusinessRoadmap(Base, TimestampMixin, SoftDeleteMixin):
    """Business development roadmap with stages."""
    __tablename__ = "business_roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    business: Mapped["Business"] = relationship("Business", back_populates="roadmap")
    stages: Mapped[List["RoadmapStage"]] = relationship(
        "RoadmapStage", back_populates="roadmap", cascade="all, delete-orphan",
        order_by="RoadmapStage.order_index"
    )

class RoadmapStage(Base, TimestampMixin, SoftDeleteMixin):
    """Individual stage in a business roadmap."""
    __tablename__ = "roadmap_stages"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("business_roadmaps.id", ondelete="CASCADE"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_type: Mapped[StageType] = mapped_column(Enum(StageType), nullable=False)
    status: Mapped[RoadmapStageStatus] = mapped_column(
        Enum(RoadmapStageStatus), default=RoadmapStageStatus.PLANNED
    )
    output_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    roadmap: Mapped["BusinessRoadmap"] = relationship("BusinessRoadmap", back_populates="stages")
    agent_runs: Mapped[List["AgentRun"]] = relationship(
        "AgentRun", back_populates="stage", cascade="all, delete-orphan"
    )
