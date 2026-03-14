from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    content = Column(Text, nullable=False)
    vector = Column(String) # For now storing as string, or use pgvector if available
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="embeddings")
    agent = relationship("Agent", back_populates="embeddings")
