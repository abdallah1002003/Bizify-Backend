import uuid

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UserSkill(Base):
    """
    SQLAlchemy model representing a self-declared skill level for a User.
    """

    __tablename__ = "user_skills"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    skill_name = Column(String, nullable = False)
    declared_level = Column(Integer, nullable = False)
