import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class PlatformSetting(Base):
    """Admin-managed key/value platform settings, overriding env-var defaults."""

    __tablename__ = "platform_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String, nullable=True)
