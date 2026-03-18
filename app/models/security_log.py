import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SecurityLog(Base):
    """
    SQLAlchemy model representing security-related event logs.
    """

    __tablename__ = "security_logs"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = True)
    event_type = Column(String, nullable = False)
    details = Column(JSON, nullable = True)
    ip_address = Column(String, nullable = True)
    created_at = Column(DateTime, default = datetime.utcnow)

    user = relationship("User")
