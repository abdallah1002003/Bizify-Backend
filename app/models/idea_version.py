from sqlalchemy import Column, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class IdeaVersion(Base):
    __tablename__ = "idea_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idea_id = Column(UUID(as_uuid=True), ForeignKey("ideas.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    snapshot_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    idea = relationship("Idea", back_populates="versions")
    creator = relationship("User")
