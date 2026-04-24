from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ── Predefined Skill ──────────────────────────────────────────────────────────

class PredefinedSkillRead(BaseModel):
    """A skill that belongs to a category and can be selected by an entrepreneur."""

    id: UUID
    name: str
    category_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PredefinedSkillSearchResult(BaseModel):
    """Search result that includes category name for context."""

    id: UUID
    name: str
    category_id: UUID
    category_name: str

    model_config = ConfigDict(from_attributes=True)


# ── Skill Category ────────────────────────────────────────────────────────────

class SkillCategoryRead(BaseModel):
    """A category with its list of predefined skills."""

    id: UUID
    name: str
    description: Optional[str] = None
    predefined_skills: List[PredefinedSkillRead] = []

    model_config = ConfigDict(from_attributes=True)


# ── User Skill ────────────────────────────────────────────────────────────────

class UserSkillCreate(BaseModel):
    """
    Payload to add a skill to the current user.

    Two valid scenarios:
      1. Pick from predefined list  → send predefined_skill_id (skill_name is auto-filled).
      2. Custom skill               → send skill_name only (predefined_skill_id stays None).
    """

    predefined_skill_id: Optional[UUID] = None
    skill_name: Optional[str] = None       # required only when adding a custom skill

    def is_custom(self) -> bool:
        return self.predefined_skill_id is None


class UserSkillRead(BaseModel):
    """A skill attached to a user's profile."""

    id: UUID
    user_id: UUID
    skill_name: str
    is_custom: bool
    predefined_skill_id: Optional[UUID] = None
    category_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# keep old name as alias so existing imports don't break immediately
UserSkill = UserSkillRead

