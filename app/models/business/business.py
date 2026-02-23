import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, JSON, Float, Integer
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import BusinessStage, CollaboratorRole, InviteStatus, StageType, RoadmapStageStatus
from app.core.crud_utils import _utc_now as utc_now

class Business(Base):
    __tablename__ = "businesses"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id = Column(GUID, ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True, unique=True)
    owner_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stage = Column(Enum(BusinessStage), default=BusinessStage.EARLY)
    context_json = Column(JSON, nullable=True)
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    idea_backref = relationship("Idea", foreign_keys="[Idea.business_id]", back_populates="business")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="businesses")
    collaborators = relationship("BusinessCollaborator", back_populates="business", cascade="all, delete-orphan")
    invites = relationship("BusinessInvite", back_populates="business", cascade="all, delete-orphan")
    roadmap = relationship("BusinessRoadmap", back_populates="business", uselist=False, cascade="all, delete-orphan")
    partner_requests = relationship("PartnerRequest", back_populates="business", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="business", cascade="all, delete-orphan")
    idea_accesses = relationship("IdeaAccess", back_populates="business", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", foreign_keys="ChatSession.business_id", back_populates="business", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", foreign_keys="ShareLink.business_id", back_populates="business", cascade="all, delete-orphan")

class BusinessCollaborator(Base):
    __tablename__ = "business_collaborators"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    business_id = Column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(CollaboratorRole), nullable=False)
    added_at = Column(DateTime(timezone=True), default=utc_now)

    business = relationship("Business", back_populates="collaborators")
    user = relationship("User", foreign_keys=[user_id])

class BusinessInvite(Base):
    __tablename__ = "business_invites"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    business_id = Column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(InviteStatus), default=InviteStatus.PENDING)
    invited_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    business = relationship("Business", back_populates="invites")
    inviter = relationship("User", foreign_keys=[invited_by], back_populates="business_invites_sent")
    ideas_invited_for = relationship("BusinessInviteIdea", back_populates="invite", cascade="all, delete-orphan")

class BusinessInviteIdea(Base):
    __tablename__ = "business_invite_ideas"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    invite_id = Column(GUID, ForeignKey("business_invites.id", ondelete="CASCADE"), nullable=False)
    idea_id = Column(GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False)

    invite = relationship("BusinessInvite", back_populates="ideas_invited_for")
    idea = relationship("Idea", back_populates="business_invites")


class BusinessRoadmap(Base):
    __tablename__ = "business_roadmaps"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    business_id = Column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    completion_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    business = relationship("Business", back_populates="roadmap")
    stages = relationship("RoadmapStage", back_populates="roadmap", cascade="all, delete-orphan", order_by="RoadmapStage.order_index")

class RoadmapStage(Base):
    __tablename__ = "roadmap_stages"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(GUID, ForeignKey("business_roadmaps.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)
    stage_type = Column(Enum(StageType), nullable=False)
    status = Column(Enum(RoadmapStageStatus), default=RoadmapStageStatus.PLANNED)
    output_json = Column(JSON, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    roadmap = relationship("BusinessRoadmap", back_populates="stages")
    agent_runs = relationship("AgentRun", back_populates="stage", cascade="all, delete-orphan")
