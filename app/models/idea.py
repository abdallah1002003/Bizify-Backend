import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class IdeaStatus(str, enum.Enum):
    """
    Enumeration of statuses for a business idea.
    """

    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    CONVERTED = "CONVERTED"


class Idea(Base):
    """
    SQLAlchemy model representing a Business Idea in the system.
    """

    __tablename__ = "ideas"

    id = Column(UUID(as_uuid=True), primary_key = True, default = uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable = False)
    
    # Can be null until conversion
    business_id = Column(
        UUID(as_uuid = True), 
        ForeignKey("businesses.id", use_alter = True, name = "fk_idea_business_id")
    ) 
    
    title = Column(String, nullable = False)
    description = Column(Text)
    
    status = Column(
        Enum(IdeaStatus, values_callable = lambda x: [e.value for e in x]), 
        default = IdeaStatus.DRAFT
    )
    
    ai_score = Column(Float)
    is_score_outdated = Column(Boolean, default = False)
    is_archived = Column(Boolean, default = False)
    
    archived_at = Column(DateTime)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)
    converted_at = Column(DateTime)

    owner = relationship("User", back_populates = "ideas")
    business = relationship("Business", foreign_keys = [business_id])
    
    versions = relationship("IdeaVersion", back_populates = "idea")
    metrics = relationship("IdeaMetric", back_populates = "idea")
    experiments = relationship("Experiment", back_populates = "idea")
    share_links = relationship("ShareLink", back_populates = "idea")
    chat_sessions = relationship("ChatSession", back_populates = "idea")
    comparison_items = relationship("ComparisonItem", back_populates = "idea")
