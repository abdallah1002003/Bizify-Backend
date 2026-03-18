import uuid

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Usage(Base):
    """
    SQLAlchemy model representing resource usage by a User.
    """

    __tablename__ = "usages"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    # e.g., "ai_tokens", "file_storage"
    resource_type = Column(String, nullable = False)
    used = Column(Integer, default = 0)
    limit_value = Column(Integer)

    user = relationship("User", back_populates = "usages")
