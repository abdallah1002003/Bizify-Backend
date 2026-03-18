import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AuditLog(Base):
    """
    SQLAlchemy model representing a record of user actions for audit purposes.
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id", ondelete = "SET NULL"), nullable = True)

    action = Column(String, nullable = False)
    details = Column(JSON, nullable = True)
    ip_address = Column(String, nullable = True)
    created_at = Column(DateTime, default = datetime.utcnow)
