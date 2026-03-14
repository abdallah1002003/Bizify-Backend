from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class BusinessStage(str, enum.Enum):
    EARLY = "early"
    BUILDING = "building"
    SCALING = "scaling"

class Business(Base):
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idea_id = Column(UUID(as_uuid=True), ForeignKey("ideas.id", use_alter=True, name="fk_business_idea_id")) # Reference to source idea
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    stage = Column(Enum(BusinessStage), default=BusinessStage.EARLY)
    context_json = Column(JSON)
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="businesses")
    converted_idea = relationship("Idea", foreign_keys=[idea_id])
    collaborators = relationship("BusinessCollaborator", back_populates="business")
    invites = relationship("BusinessInvite", back_populates="business")
    roadmap = relationship("BusinessRoadmap", back_populates="business", uselist=False)
    partner_requests = relationship("PartnerRequest", back_populates="business")
    embeddings = relationship("Embedding", back_populates="business")
    chat_sessions = relationship("ChatSession", back_populates="business")
    share_links = relationship("ShareLink", back_populates="business")
