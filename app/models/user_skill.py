import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserSkill(Base):
    """
    Represents a skill selected (or manually entered) by an Entrepreneur.

    - predefined_skill_id: set when the user picks from a predefined list.
    - skill_name:          always present; copied from PredefinedSkill.name
                           or typed manually when is_custom=True.
    - is_custom:           True when the entrepreneur typed a skill not in the list.
    - category_id:         optional link to SkillCategory (NULL for fully custom skills).
    """

    __tablename__ = "user_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String, nullable=False)
    is_custom = Column(Boolean, default=False, nullable=False)

    # optional – NULL when the skill was typed manually
    predefined_skill_id = Column(
        UUID(as_uuid=True),
        ForeignKey("predefined_skills.id", ondelete="SET NULL"),
        nullable=True,
    )
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("skill_categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    predefined_skill = relationship("PredefinedSkill")
    category = relationship("SkillCategory")

