import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ShareLinkBase(BaseModel):
    idea_id: Optional[uuid.UUID] = None
    business_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID
    token: str
    is_public: Optional[bool] = False
    expires_at: Optional[datetime] = None


class ShareLinkRead(ShareLinkBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ShareRequest(BaseModel):
    idea_ids: list[uuid.UUID]
    # How long the link stays valid. Omitted → server default (90 days).
    # Clamped server-side to [1, 365].
    expires_in_days: Optional[int] = None


class ShareItem(BaseModel):
    idea_id: uuid.UUID
    idea_title: str
    token: str
    share_url: str
    expires_at: Optional[datetime] = None


class ShareResponse(BaseModel):
    items: list[ShareItem]


class SharedIdeaRead(BaseModel):
    # Core idea fields
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str
    budget: Optional[float] = None
    skills: Optional[Any] = None
    feasibility: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # AI seed metadata
    domain: Optional[str] = None
    problem_evidence: Optional[Any] = None
    core_insight: Optional[str] = None
    target_segment: Optional[str] = None
    founding_hypothesis: Optional[str] = None

    # Core AI analysis sections (each is the inner value returned by the pipeline)
    problems: Optional[Any] = None
    customers: Optional[Any] = None
    competition: Optional[Any] = None
    market_potential: Optional[Any] = None
    idea_strategy: Optional[Any] = None
    business_model: Optional[Any] = None
    functions_list: Optional[Any] = None
    mvp_planning: Optional[Any] = None
    unit_economics: Optional[Any] = None
    go_to_market: Optional[Any] = None

    # Marketing analysis sections
    customer_research: Optional[Any] = None
    copywriting: Optional[Any] = None
    pricing: Optional[Any] = None
    launch_strategy: Optional[Any] = None
    ad_creative: Optional[Any] = None
    social_media: Optional[Any] = None
    marketing_ideas: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)
