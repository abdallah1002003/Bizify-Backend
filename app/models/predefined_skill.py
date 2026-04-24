import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PredefinedSkill(Base):
    """
    A skill that belongs to a SkillCategory and is shown to entrepreneurs as a selectable option.
    Entrepreneurs can also add custom skills that are NOT in this list.
    """

    __tablename__ = "predefined_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("skill_categories.id", ondelete="CASCADE"),
        nullable=False,
    )

    category = relationship("SkillCategory", back_populates="predefined_skills")
