from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class Usage(Base):
    __tablename__ = "usages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resource_type = Column(String, nullable=False) # e.g., "ai_tokens", "file_storage"
    used = Column(Integer, default=0)
    limit_value = Column(Integer)

    user = relationship("User", back_populates="usages")
