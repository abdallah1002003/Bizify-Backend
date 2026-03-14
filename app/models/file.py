from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)
    size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="files")
