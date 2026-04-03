from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UserConceptState(Base):
    """
    Tracks the last concept viewed by a user to ensure continuity of the guidance experience.
    """

    __tablename__ = "user_concept_states"

    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), primary_key = True)
    last_viewed_concept_id = Column(
        UUID(as_uuid = True),
        ForeignKey("guidance_concepts.id"),
        nullable = False
    )
    updated_at = Column(
        DateTime,
        default = lambda: datetime.now(timezone.utc),
        onupdate = lambda: datetime.now(timezone.utc)
    )
