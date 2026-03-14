from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.business_invite import InviteStatus
from app.models.business_collaborator import CollaboratorRole

class BusinessInviteBase(BaseModel):
    business_id: UUID
    email: Optional[str] = None
    status: Optional[InviteStatus] = InviteStatus.PENDING
    role: CollaboratorRole = CollaboratorRole.VIEWER


class BusinessInviteCreate(BusinessInviteBase):
    invited_by: UUID
    expires_at: datetime

class BusinessInviteRead(BusinessInviteBase):
    id: UUID
    token: str
    invited_by: UUID
    expires_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
