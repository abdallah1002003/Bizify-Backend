import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Agent(Base):
    """
    SQLAlchemy model representing an AI Agent within the system.
    """
    
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phase = Column(String)  # e.g., "research", "strategy"

    runs = relationship("AgentRun", back_populates="agent")
    embeddings = relationship("Embedding", back_populates="agent")
