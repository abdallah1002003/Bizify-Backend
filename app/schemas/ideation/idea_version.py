from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class IdeaVersionBase(BaseModel):
    idea_id: UUID
    created_by: UUID
    snapshot_json: Optional[dict] = None

class IdeaVersionCreate(BaseModel):
    idea_id: UUID
    created_by: UUID
    snapshot_json: Optional[dict] = None

class IdeaVersionUpdate(BaseModel):
    idea_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    snapshot_json: Optional[dict] = None
    created_at: Optional[datetime] = None

class IdeaVersionResponse(IdeaVersionBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
