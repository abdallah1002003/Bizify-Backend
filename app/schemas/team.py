import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.business_collaborator import CollaboratorRole


class TeamBase(BaseModel):
    """
    Base Pydantic model for Team data.
    """
    name: str
    description: Optional[str] = None
    role: CollaboratorRole = CollaboratorRole.VIEWER


class TeamCreate(TeamBase):
    """
    Pydantic model for creating a new Team.
    """
    idea_ids: Optional[List[uuid.UUID]] = []


class TeamUpdate(BaseModel):
    """
    Pydantic model for updating an existing Team's metadata or global role.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    role: Optional[CollaboratorRole] = None


class TeamAccessUpdate(BaseModel):
    """
    Pydantic model for updating the ideas a Team can access.
    """
    idea_ids: List[uuid.UUID]


class TeamMemberRead(BaseModel):
    """
    Pydantic model for reading Team Member details.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    added_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TeamRead(TeamBase):
    """
    Pydantic model for reading Team data, including its members and basic details.
    """
    id: uuid.UUID
    business_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    members_count: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)
