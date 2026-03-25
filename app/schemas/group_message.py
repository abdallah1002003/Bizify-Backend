from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict

class GroupMessageBase(BaseModel):
    content: str

class GroupMessageCreate(GroupMessageBase):
    pass

class GroupMessageResponse(GroupMessageBase):
    id: uuid.UUID
    group_id: uuid.UUID
    sender_id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
