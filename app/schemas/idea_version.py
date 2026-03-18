import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class IdeaVersionRead(BaseModel):
    """
    Pydantic model for reading Idea Version data.
    """
    
    id: uuid.UUID
    idea_id: uuid.UUID
    created_by: uuid.UUID
    snapshot_json: Any
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
