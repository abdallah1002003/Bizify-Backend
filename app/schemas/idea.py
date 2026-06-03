import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.ai.idea import IdeaStatus


class ProblemEvidence(BaseModel):
    problems_analyzed: int = 0
    top_validated:     list[dict] = []
    why_this_idea:     str = ""
    primary_gap:       str = ""
    customer_signal:   str = ""

    model_config = ConfigDict(extra="allow")


class OverviewDetail(BaseModel):
    value_proposition:     str = ""
    founder_market_fit:    str = ""
    strategic_advantage:   str = ""
    execution_advantage:   str = ""
    why_now:               str = ""
    why_this_should_exist: str = ""

    model_config = ConfigDict(extra="allow")


class IdeaBase(BaseModel):
    """
    Base Pydantic model for Business Idea data.
    """

    title:               str
    description:         Optional[str]            = None
    status:              IdeaStatus                = IdeaStatus.DRAFT
    is_archived:         Optional[bool]            = False
    problem_validation_score: Optional[float]      = None
    pipeline_complete:   Optional[bool]            = None
    budget:              Optional[float]           = None
    budget_detail:       Optional[Any]             = None
    skills:              Optional[Any]             = None
    feasibility:         Optional[float]           = None
    # AI seed fields
    domain:              Optional[str]             = None
    problem_evidence:    Optional[ProblemEvidence] = None
    core_insight:        Optional[str]             = None
    target_segment:      Optional[str]             = None
    founding_hypothesis: Optional[str]             = None
    overview_detail:     Optional[OverviewDetail]  = None


    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class IdeaCreate(IdeaBase):
    """
    Pydantic model for creating a new Business Idea.
    """
    pass


class IdeaUpdate(BaseModel):
    """
    Pydantic model for updating an existing Business Idea.
    """

    title:                    Optional[str]          = None
    description:              Optional[str]          = None
    status:                   Optional[IdeaStatus]   = None
    is_archived:              Optional[bool]         = None
    problem_validation_score: Optional[float]        = None
    budget:                   Optional[float]        = None
    skills:              Optional[list[str]]        = None
    feasibility:         Optional[float]            = None
    business_id:         Optional[uuid.UUID]        = None
    domain:              Optional[str]              = None
    problem_evidence:    Optional[ProblemEvidence]  = None
    core_insight:        Optional[str]              = None
    target_segment:      Optional[str]              = None
    founding_hypothesis: Optional[str]              = None
    overview_detail:     Optional[OverviewDetail]   = None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class IdeaRead(IdeaBase):
    """
    Pydantic model for reading Business Idea data.
    """
    
    id: uuid.UUID
    owner_id: uuid.UUID
    business_id: Optional[uuid.UUID] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    converted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
