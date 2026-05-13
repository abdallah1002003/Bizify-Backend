import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class IdeaVersion(Base):
    """
    SQLAlchemy model representing a versioned snapshot of a Business Idea.
    """

    __tablename__ = "idea_versions"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    idea_id = Column(UUID(as_uuid = True), ForeignKey("ideas.id"), nullable = False)
    created_by = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    snapshot_json = Column(JSON, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    idea = relationship("Idea", back_populates = "versions")
    creator = relationship("User")
