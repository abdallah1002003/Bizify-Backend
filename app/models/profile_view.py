import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProfileView(Base):
    __tablename__ = "profile_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partner_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    viewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    viewer_name = Column(String, nullable=True)
    viewer_email = Column(String, nullable=True)
    viewer_role = Column(String, nullable=True)
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    partner = relationship("PartnerProfile", backref="profile_views")
    viewer = relationship("User", foreign_keys=[viewer_id])
