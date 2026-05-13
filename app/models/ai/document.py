import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class Document(Base):
    """
    SQLAlchemy model representing a processed document with extracted text for AI.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, index=True, nullable=False)
    content_type = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=True)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploader = relationship("User", backref="uploaded_documents")
