from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.models.business_collaborator import CollaboratorRole

class BusinessCollaboratorBase(BaseModel):
    business_id: UUID
    user_id: UUID
    role: CollaboratorRole

class BusinessCollaboratorCreate(BusinessCollaboratorBase):
    pass

class BusinessCollaboratorRead(BusinessCollaboratorBase):
    id: UUID
    added_at: datetime
    model_config = ConfigDict(from_attributes=True)
