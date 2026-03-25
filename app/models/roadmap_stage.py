import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class StageType(str, enum.Enum):
    """
    Enumeration of different types of roadmap stages.
    """

    READINESS = "READINESS"
    RESEARCH = "RESEARCH"
    STRATEGY = "STRATEGY"
    MARKET = "MARKET"
    FUNCTIONS = "FUNCTIONS"
    ECONOMICS = "ECONOMICS"
    LEGAL = "LEGAL"
    MVP = "MVP"
    BRANDING = "BRANDING"
    GTM = "GTM"
    OPERATIONS = "OPERATIONS"


class StageStatus(str, enum.Enum):
    """
    Enumeration of readiness statuses for a roadmap stage.
    """

    LOCKED = "LOCKED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class RoadmapStage(Base):
    """
    SQLAlchemy model representing a specific stage within a Business Roadmap.
    """

    __tablename__ = "roadmap_stages"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    roadmap_id = Column(
        UUID(as_uuid = True),
        ForeignKey("business_roadmaps.id"),
        nullable = False
    )
    order_index = Column(Integer, nullable = False)
    stage_type = Column(
        Enum(StageType, values_callable = lambda x: [e.value for e in x]),
        nullable = False
    )
    status = Column(
        Enum(StageStatus, values_callable = lambda x: [e.value for e in x]),
        default = StageStatus.LOCKED
    )
    output_json = Column(JSON)
    completed_at = Column(DateTime)

    roadmap = relationship("BusinessRoadmap", back_populates = "stages")
    agent_runs = relationship("AgentRun", back_populates = "stage")
