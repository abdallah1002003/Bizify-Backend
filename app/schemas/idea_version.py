from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Any

class IdeaVersionRead(BaseModel):
    id: UUID
    idea_id: UUID
    created_by: UUID
    snapshot_json: Any
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
