from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idea_id = Column(UUID(as_uuid=True), ForeignKey("ideas.id"))
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    is_public = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    idea = relationship("Idea", back_populates="share_links")
    business = relationship("Business", back_populates="share_links")
    creator = relationship("User", back_populates="share_links")
