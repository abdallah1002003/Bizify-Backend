from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class StageType(str, enum.Enum):
    READINESS = "readiness"
    RESEARCH = "research"
    STRATEGY = "strategy"
    MARKET = "market"
    FUNCTIONS = "functions"
    ECONOMICS = "economics"
    LEGAL = "legal"
    MVP = "mvp"
    BRANDING = "branding"
    GTM = "gtm"
    OPERATIONS = "operations"

class StageStatus(str, enum.Enum):
    LOCKED = "locked"
    ACTIVE = "active"
    COMPLETED = "completed"

class RoadmapStage(Base):
    __tablename__ = "roadmap_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("business_roadmaps.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    stage_type = Column(Enum(StageType), nullable=False)
    status = Column(Enum(StageStatus), default=StageStatus.LOCKED)
    output_json = Column(JSON)
    completed_at = Column(DateTime)

    roadmap = relationship("BusinessRoadmap", back_populates="stages")
    agent_runs = relationship("AgentRun", back_populates="stage")
