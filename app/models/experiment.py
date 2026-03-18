import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Experiment(Base):
    """
    SQLAlchemy model representing an Experiment related to a Business Idea.
    """

    __tablename__ = "experiments"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    idea_id = Column(UUID(as_uuid = True), ForeignKey("ideas.id"), nullable = False)
    created_by = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    hypothesis = Column(String, nullable = False)
    status = Column(String)
    result_summary = Column(Text)
    created_at = Column(DateTime, default = datetime.utcnow)

    idea = relationship("Idea", back_populates = "experiments")
    creator = relationship("User")
