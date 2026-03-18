import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ShareLinkBase(BaseModel):
    """
    Base Pydantic model for Share Link data.
    """
    
    idea_id: Optional[uuid.UUID] = None
    business_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID
    token: str
    is_public: Optional[bool] = False
    expires_at: Optional[datetime] = None


class ShareLinkRead(ShareLinkBase):
    """
    Pydantic model for reading Share Link data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
