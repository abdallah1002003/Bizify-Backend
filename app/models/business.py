import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class BusinessStage(str, enum.Enum):
    """
    Enumeration of different stages of a business life cycle.
    """

    EARLY = "EARLY"
    BUILDING = "BUILDING"
    SCALING = "SCALING"


class Business(Base):
    """
    SQLAlchemy model representing a Business entity in the system.
    """

    __tablename__ = "businesses"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    
    # Reference to source idea
    idea_id = Column(
        UUID(as_uuid = True), 
        ForeignKey("ideas.id", use_alter = True, name = "fk_business_idea_id")
    ) 
    
    owner_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    
    stage = Column(
        Enum(BusinessStage, values_callable = lambda x: [e.value for e in x]), 
        default = BusinessStage.EARLY
    )
    
    context_json = Column(JSON)
    is_archived = Column(Boolean, default = False)
    archived_at = Column(DateTime)
    
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)
    
    industry_id = Column(UUID(as_uuid = True), ForeignKey("industries.id"), nullable = True)

    owner = relationship("User", back_populates = "businesses")
    converted_idea = relationship("Idea", foreign_keys = [idea_id])
    # A generic "groups" relationship that replaces previous direct collaborators
    groups = relationship("Group", back_populates = "business", cascade="all, delete-orphan", uselist = False)
    roadmap = relationship("BusinessRoadmap", back_populates = "business", uselist = False)
    partner_requests = relationship("PartnerRequest", back_populates = "business")
    embeddings = relationship("Embedding", back_populates = "business")
    chat_sessions = relationship("ChatSession", back_populates = "business")
    share_links = relationship("ShareLink", back_populates = "business")
    industry = relationship("Industry", back_populates = "businesses")
