import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Embedding(Base):
    """
    SQLAlchemy model representing a vector embedding for Business context.
    """

    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    business_id = Column(UUID(as_uuid = True), ForeignKey("businesses.id"), nullable = False)
    agent_id = Column(UUID(as_uuid = True), ForeignKey("agents.id"), nullable = False)
    content = Column(Text, nullable = False)
    # Stored as string until pgvector is available
    vector = Column(String)
    created_at = Column(DateTime, default = datetime.utcnow)

    business = relationship("Business", back_populates = "embeddings")
    agent = relationship("Agent", back_populates = "embeddings")
