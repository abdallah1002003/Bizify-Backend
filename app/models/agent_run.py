import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RunStatus(str, enum.Enum):
    """
    Enumeration of statuses for an AI agent run.
    """
    
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"


class AgentRun(Base):
    """
    SQLAlchemy model representing the execution of an AI Agent.
    """
    
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("roadmap_stages.id"), 
        nullable=False
    )
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    confidence_score = Column(Float)
    status = Column(Enum(RunStatus, values_callable=lambda x: [e.value for e in x]))
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    stage = relationship("RoadmapStage", back_populates="agent_runs")
    agent = relationship("Agent", back_populates="runs")
    validation_logs = relationship("ValidationLog", back_populates="agent_run")
