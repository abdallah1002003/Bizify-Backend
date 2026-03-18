import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminActionLogRead(BaseModel):
    """
    Pydantic model for reading Administrative Action Logs.
    """
    
    id: uuid.UUID
    admin_id: uuid.UUID
    action_type: str
    target_entity: str
    target_id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
