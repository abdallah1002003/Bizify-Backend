import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProfileVisibility(str, enum.Enum):
    """
    Enumeration of visibility levels for a user profile.
    """

    PUBLIC = "public"
    PRIVATE = "private"
    TEAM_ONLY = "team_only"


class PrivacySetting(Base):
    """
    SQLAlchemy model representing a user's privacy preferences.
    """

    __tablename__ = "privacy_settings"

    user_id = Column(
        UUID(as_uuid = True),
        ForeignKey("users.id", ondelete = "CASCADE"),
        primary_key = True
    )
    visibility = Column(Enum(ProfileVisibility), default = ProfileVisibility.PUBLIC)
    show_contact_info = Column(Boolean, default = True)

    user = relationship("User", back_populates = "privacy_settings")
