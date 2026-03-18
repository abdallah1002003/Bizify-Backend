import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.business_collaborator import CollaboratorRole, CollaboratorStatus


class BusinessCollaboratorBase(BaseModel):
    """
    Base Pydantic model for Business Collaborator data.
    """
    
    business_id: uuid.UUID
    user_id: uuid.UUID
    role: CollaboratorRole


class BusinessCollaboratorCreate(BusinessCollaboratorBase):
    """
    Pydantic model for creating a Business Collaborator.
    """
    
    pass


class BusinessCollaboratorRead(BusinessCollaboratorBase):
    """
    Pydantic model for reading Business Collaborator data.
    """
    
    id: uuid.UUID
    added_at: datetime
    status: CollaboratorStatus
    
    model_config = ConfigDict(from_attributes=True)


class BusinessMemberRead(BaseModel):
    """
    Pydantic model for a team member in the listing view (UC_19).
    Includes dynamic permission flags based on the requester's role.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    role: CollaboratorRole
    status: CollaboratorStatus
    added_at: datetime
    
    can_remove: bool = False
    can_change_role: bool = False

    model_config = ConfigDict(from_attributes=True)
