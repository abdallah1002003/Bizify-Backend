from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserSkillBase(BaseModel):
    """
    Base Pydantic model for user skill data.
    """

    skill_name: str
    declared_level: int = Field(..., ge = 1, le = 5)


class UserSkillCreate(UserSkillBase):
    """
    Pydantic model for creating a user skill.
    """

    pass


class UserSkill(UserSkillBase):
    """
    Pydantic model representing a user skill.
    """

    id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes = True)






