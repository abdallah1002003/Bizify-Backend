import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
)
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
    
    problem_validation_score = Column(Float)
    budget = Column(Float)
    budget_detail = Column(JSON)   # {amount_egp, is_estimate, basis, breakdown, note, source}
    skills = Column(JSON)
    feasibility = Column(Float)
    is_score_outdated    = Column(Boolean, default = False)
    is_archived          = Column(Boolean, default = False)
    pipeline_complete    = Column(Boolean, default = False)

    archived_at         = Column(DateTime)
    created_at          = Column(DateTime, default = datetime.utcnow)
    updated_at          = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)
    converted_at        = Column(DateTime)

    # AI-generated seed fields
    domain              = Column(String,  nullable = True)
    problem_evidence    = Column(JSON,    nullable = True)
    core_insight        = Column(Text,    nullable = True)
    target_segment      = Column(Text,    nullable = True)
    founding_hypothesis = Column(Text,    nullable = True)
    overview_detail     = Column(JSON,    nullable = True)

    owner = relationship("User", back_populates = "ideas")
    business = relationship("Business", foreign_keys = [business_id])
    
    versions = relationship("IdeaVersion", back_populates = "idea")
    metrics = relationship("IdeaMetric", back_populates = "idea")
    experiments = relationship("Experiment", back_populates = "idea")
    share_links = relationship("ShareLink", back_populates = "idea")
    chat_sessions = relationship("ChatSession", back_populates = "idea")
    comparison_items = relationship("ComparisonItem", back_populates = "idea")
    agent_runs = relationship("AgentRun", back_populates = "idea")
