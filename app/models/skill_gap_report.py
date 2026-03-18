import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, JSON, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class SkillGapReport(Base):
    """
    SQLAlchemy model representing a Skill Gap Analysis report for a user.
    """

    __tablename__ = "skill_gap_reports"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), unique = True, nullable = False)
    
    report_data = Column(JSON, nullable = False)
    accuracy_status = Column(String, default = "accurate") 
    risk_level = Column(String, nullable = False)
    
    is_outdated = Column(Boolean, default = False)
    
    updated_at = Column(
        DateTime, 
        default = lambda: datetime.now(timezone.utc), 
        onupdate = lambda: datetime.now(timezone.utc)
    )
