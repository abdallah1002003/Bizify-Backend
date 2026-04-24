import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SkillCategory(Base):
    """
    Represents a top-level skill category (e.g. 'Technology', 'Marketing').
    Each category contains a set of predefined skills that entrepreneurs can pick from.
    """

    __tablename__ = "skill_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)

    predefined_skills = relationship(
        "PredefinedSkill", back_populates="category", cascade="all, delete-orphan"
    )
