from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

class AgentBase(BaseModel):
    name: str
    phase: Optional[str] = None

class AgentCreate(AgentBase):
    pass

class AgentRead(AgentBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
