import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class File(Base):
    """
    SQLAlchemy model representing a File uploaded by a user.
    """

    __tablename__ = "files"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    owner_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    file_path = Column(String, nullable = False)
    file_type = Column(String)
    size = Column(Integer)
    uploaded_at = Column(DateTime, default = datetime.utcnow)

    owner = relationship("User", back_populates = "files")
