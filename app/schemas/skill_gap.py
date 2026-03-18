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


class SkillGapDetail(BaseModel):
    """
    Pydantic model for detailed skill gap analysis.
    """

    skill_name: str
    declared_level: int
    minimum_required_level: int
    gap_size: int
    severity: str
    status: str
    recommendation: str


class SkillGapReportResponse(BaseModel):
    """
    Pydantic model for a skill gap report response.
    """

    user_id: UUID
    report_data: List[SkillGapDetail]
    accuracy_status: str
    risk_level: str
    is_outdated: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes = True)


class UserSkillsInput(BaseModel):
    """
    Pydantic model for bulk user skills input.
    """

    skills: List[UserSkillBase]


class SkillBenchmarkCreate(BaseModel):
    """
    Pydantic model for creating a skill benchmark.
    """

    skill_name: str
    industry_id: UUID
    minimum_required_level: int = Field(..., ge = 1, le = 5)
    weight: float = Field(default = 1.0, ge = 0.5, le = 2.0)


class SkillBenchmarkResponse(SkillBenchmarkCreate):
    """
    Pydantic model for a skill benchmark response.
    """

    id: UUID

    model_config = ConfigDict(from_attributes = True)


class IndustryBase(BaseModel):
    """
    Base Pydantic model for industry data.
    """

    name: str
    parent_id: Optional[UUID] = None
    level: int = 1


class IndustryCreate(IndustryBase):
    """
    Pydantic model for creating an industry.
    """

    pass


class IndustryResponse(IndustryBase):
    """
    Pydantic model for an industry response.
    """

    id: UUID

    model_config = ConfigDict(from_attributes = True)
