import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ExportStatus(str, enum.Enum):
    """
    Enumeration of lifecycle statuses for a data export job.
    """

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ExportJob(Base):
    """
    SQLAlchemy model representing a background data export job.
    """

    __tablename__ = "export_jobs"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)

    scope = Column(JSON, nullable = False)
    format = Column(String, nullable = False)

    status = Column(Enum(ExportStatus), default = ExportStatus.PENDING)
    storage_path = Column(String, nullable = True)
    task_id = Column(String, nullable = True)

    error_details = Column(JSON, nullable = True)

    completed_at = Column(DateTime, nullable = True)
    created_at = Column(DateTime, default = datetime.utcnow)
