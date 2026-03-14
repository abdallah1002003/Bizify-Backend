from sqlalchemy import Column, Boolean, DateTime, Text, JSON, ForeignKey , Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import enum
from datetime import datetime



class GuideStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    COMPLETED = "completed"
    POSTPONED = "postponed"
    SKIPPED = "skipped"

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bio = Column(Text)
    skills_json = Column(JSON)
    guide_status = Column(Enum(GuideStatus), default=GuideStatus.NOT_STARTED)
    interests_json = Column(JSON)
    preferences_json = Column(JSON)
    risk_profile_json = Column(JSON)
    onboarding_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    background_json = Column(JSON)
    personality_json = Column(JSON)
    personalization_profile = Column(Text)

    user = relationship("User", back_populates="profile")
