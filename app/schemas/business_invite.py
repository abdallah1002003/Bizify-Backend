import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.business_collaborator import CollaboratorRole
from app.models.business_invite import InviteStatus


class BusinessInviteBase(BaseModel):
    """
    Base Pydantic model for Business Invite data.
    """
    
    business_id: uuid.UUID
    email: Optional[str] = None
    status: Optional[InviteStatus] = InviteStatus.PENDING
    role: CollaboratorRole = CollaboratorRole.VIEWER


class BusinessInviteCreate(BusinessInviteBase):
    """
    Pydantic model for creating a Business Invite.
    """
    
    invited_by: uuid.UUID
    expires_at: datetime


class BusinessInviteRead(BusinessInviteBase):
    """
    Pydantic model for reading Business Invite data.
    """
    
    id: uuid.UUID
    token: str
    invited_by: uuid.UUID
    expires_at: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
