import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AdminActionLog(Base):
    """
    SQLAlchemy model representing logs of administrative actions.
    """
    
    __tablename__ = "admin_action_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action_type = Column(String, nullable=False)
    target_entity = Column(String, nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    admin = relationship("User", back_populates="admin_logs")
