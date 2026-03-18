import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ValidationLog(Base):
    """
    SQLAlchemy model representing a log of an AI agent's validation stage.
    """

    __tablename__ = "validation_logs"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    agent_run_id = Column(
        UUID(as_uuid = True),
        ForeignKey("agent_runs.id"),
        nullable = False
    )
    confidence_score = Column(Float)
    critique_json = Column(JSON)
    threshold_passed = Column(Boolean)
    created_at = Column(DateTime, default = datetime.utcnow)

    agent_run = relationship("AgentRun", back_populates = "validation_logs")
