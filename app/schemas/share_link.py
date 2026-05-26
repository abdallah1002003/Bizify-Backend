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


class ShareItem(BaseModel):
    idea_id: uuid.UUID
    idea_title: str
    token: str
    share_url: str


class ShareResponse(BaseModel):
    items: list[ShareItem]


class SharedIdeaRead(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str
    budget: Optional[float] = None
    skills: Optional[Any] = None
    feasibility: Optional[float] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
