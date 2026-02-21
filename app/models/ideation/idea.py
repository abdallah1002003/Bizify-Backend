import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Float
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import IdeaStatus

def utc_now():
    return datetime.now(timezone.utc)

class Idea(Base):
    __tablename__ = "ideas"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    owner_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(GUID, ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(IdeaStatus), default=IdeaStatus.DRAFT)
    ai_score = Column(Float, nullable=True)
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    owner = relationship("User", foreign_keys=[owner_id], back_populates="ideas")
    business = relationship("Business", foreign_keys=[business_id], back_populates="idea_backref")
    versions = relationship("IdeaVersion", back_populates="idea", cascade="all, delete-orphan")
    metrics = relationship("IdeaMetric", back_populates="idea", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="idea", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", foreign_keys="ChatSession.idea_id", back_populates="idea", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", foreign_keys="ShareLink.idea_id", back_populates="idea", cascade="all, delete-orphan")
    comparisons = relationship("ComparisonItem", back_populates="idea", cascade="all, delete-orphan")
    accesses = relationship("IdeaAccess", back_populates="idea", cascade="all, delete-orphan")
    business_invites = relationship("BusinessInviteIdea", back_populates="idea", cascade="all, delete-orphan")

class IdeaVersion(Base):
    __tablename__ = "idea_versions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id = Column(GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    snapshot_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    idea = relationship("Idea", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])

class IdeaMetric(Base):
    __tablename__ = "idea_metrics"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id = Column(GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=utc_now)

    idea = relationship("Idea", back_populates="metrics")
    creator = relationship("User", foreign_keys=[created_by])

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id = Column(GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    hypothesis = Column(String, nullable=False)
    status = Column(String, nullable=False)
    result_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    idea = relationship("Idea", back_populates="experiments")
    creator = relationship("User", foreign_keys=[created_by])

class IdeaAccess(Base):
    __tablename__ = "idea_accesses"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    idea_id = Column(GUID, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_experiment = Column(Boolean, default=False)
    assigned_job = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    idea = relationship("Idea", back_populates="accesses")
    business = relationship("Business", back_populates="idea_accesses")
    user = relationship("User", foreign_keys=[user_id], back_populates="idea_accesses")
