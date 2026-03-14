from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class ShareLinkBase(BaseModel):
    idea_id: Optional[UUID] = None
    business_id: Optional[UUID] = None
    created_by: UUID
    token: str
    is_public: Optional[bool] = False
    expires_at: Optional[datetime] = None

class ShareLinkRead(ShareLinkBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
