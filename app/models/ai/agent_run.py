import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RunStatus(str, enum.Enum):
    """
    Enumeration of statuses for an AI agent run.
    """

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    WARNING = "WARNING"


class AgentAIType(str, enum.Enum):
    """
    Enumeration of AI workflow areas tracked in the unified agent run log.
    """

    BUSINESS_ROADMAP = "BUSINESS_ROADMAP"
    ROADMAP_STAGE = "ROADMAP_STAGE"
    CHAT_SESSION = "CHAT_SESSION"
    CHAT_MESSAGE = "CHAT_MESSAGE"
    IDEA_ANALYSIS = "IDEA_ANALYSIS"
    IDEA_METRIC = "IDEA_METRIC"
    IDEA_COMPARISON = "IDEA_COMPARISON"
    COMPARISON_METRIC = "COMPARISON_METRIC"
    EXPERIMENT_RESULT = "EXPERIMENT_RESULT"
    VALIDATION_LOG = "VALIDATION_LOG"
    GENERAL = "GENERAL"


class AgentRun(Base):
    """
    SQLAlchemy model representing a unified execution log for AI work.
    """

    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ai_type = Column(
        Enum(AgentAIType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AgentAIType.ROADMAP_STAGE,
        index=True,
    )
    roadmap_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business_roadmaps.id"),
        nullable=True,
    )
    stage_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roadmap_stages.id"),
        nullable=True,
    )
    chat_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id"),
        nullable=True,
    )
    chat_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_messages.id"),
        nullable=True,
    )
    idea_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ideas.id"),
        nullable=True,
    )
    idea_metric_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idea_metrics.id"),
        nullable=True,
    )
    idea_comparison_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idea_comparisons.id"),
        nullable=True,
    )
    comparison_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("comparison_items.id"),
        nullable=True,
    )
    comparison_metric_id = Column(
        UUID(as_uuid=True),
        ForeignKey("comparison_metrics.id"),
        nullable=True,
    )
    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id"),
        nullable=True,
    )
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    input_data = Column(JSON)
    output_data = Column(JSON)
    confidence_score = Column(Float)
    status = Column(Enum(RunStatus, values_callable=lambda x: [e.value for e in x]))
    execution_time_ms = Column(Integer)
    critique_json = Column(JSON, nullable=True)
    threshold_passed = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    roadmap = relationship("BusinessRoadmap", back_populates="agent_runs")
    stage = relationship("RoadmapStage", back_populates="agent_runs")
    chat_session = relationship("ChatSession", back_populates="agent_runs")
    chat_message = relationship("ChatMessage", back_populates="agent_runs")
    idea = relationship("Idea", back_populates="agent_runs")
    idea_metric = relationship("IdeaMetric", back_populates="agent_runs")
    idea_comparison = relationship("IdeaComparison", back_populates="agent_runs")
    comparison_item = relationship("ComparisonItem", back_populates="agent_runs")
    comparison_metric = relationship("ComparisonMetric", back_populates="agent_runs")
    experiment = relationship("Experiment", back_populates="agent_runs")
    agent = relationship("Agent", back_populates="runs")

