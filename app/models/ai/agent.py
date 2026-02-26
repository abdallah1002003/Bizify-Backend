import uuid
from typing import Any, List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.guid import GUID
from app.db.database import Base
from app.models.enums import AgentRunStatus
from app.core.crud_utils import _utc_now as utc_now

if TYPE_CHECKING:
    from app.models import Business, RoadmapStage

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover
    from sqlalchemy.types import TypeDecorator

    class FallbackVector(TypeDecorator):
        """Fallback vector type when pgvector is unavailable."""

        impl = JSON
        cache_ok = True

        def __init__(self, dimensions: int, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.dimensions = dimensions

    Vector = FallbackVector


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phase: Mapped[str] = mapped_column(String, nullable=False)

    runs: Mapped[List["AgentRun"]] = relationship("AgentRun", back_populates="agent", cascade="all, delete-orphan")
    embeddings: Mapped[List["Embedding"]] = relationship("Embedding", back_populates="agent", cascade="all, delete-orphan")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("roadmap_stages.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[AgentRunStatus] = mapped_column(Enum(AgentRunStatus), default=AgentRunStatus.PENDING)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    stage: Mapped["RoadmapStage"] = relationship("RoadmapStage", back_populates="agent_runs")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="runs")
    validation_logs: Mapped[List["ValidationLog"]] = relationship("ValidationLog", back_populates="agent_run", cascade="all, delete-orphan")


class ValidationLog(Base):
    __tablename__ = "validation_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    critique_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    threshold_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    agent_run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="validation_logs")


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    vector: Mapped[Any] = mapped_column(Vector(1536), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    business: Mapped[Optional["Business"]] = relationship("Business", back_populates="embeddings")
    agent: Mapped[Optional["Agent"]] = relationship("Agent", back_populates="embeddings")
