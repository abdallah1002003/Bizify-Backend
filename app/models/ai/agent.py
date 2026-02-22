import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Float, Integer
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import AgentRunStatus

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover
    from sqlalchemy.types import TypeDecorator

    class Vector(TypeDecorator):  # type: ignore[misc]
        """Fallback vector type when pgvector is unavailable."""

        impl = JSON
        cache_ok = True

        def __init__(self, dimensions: int, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.dimensions = dimensions

def utc_now():
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phase = Column(String, nullable=False)

    runs = relationship("AgentRun", back_populates="agent", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="agent", cascade="all, delete-orphan")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    stage_id = Column(GUID, ForeignKey("roadmap_stages.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    status = Column(Enum(AgentRunStatus), default=AgentRunStatus.WARNING)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    stage = relationship("RoadmapStage", back_populates="agent_runs")
    agent = relationship("Agent", back_populates="runs")
    validation_logs = relationship("ValidationLog", back_populates="agent_run", cascade="all, delete-orphan")


class ValidationLog(Base):
    __tablename__ = "validation_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    agent_run_id = Column(GUID, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False)
    confidence_score = Column(Float, nullable=True)
    critique_json = Column(JSON, nullable=True)
    threshold_passed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    agent_run = relationship("AgentRun", back_populates="validation_logs")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    business_id = Column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    vector = Column(Vector(1536), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    business = relationship("Business", back_populates="embeddings")
    agent = relationship("Agent", back_populates="embeddings")
