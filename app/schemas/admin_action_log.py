from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class AdminActionLogRead(BaseModel):
    id: UUID
    admin_id: UUID
    action_type: str
    target_entity: str
    target_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
