import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AgentBase(BaseModel):
    """
    Base Pydantic model for AI Agent data.
    """
    
    name: str
    phase: Optional[str] = None


class AgentCreate(AgentBase):
    """
    Pydantic model for creating a new AI Agent.
    """
    
    pass


class AgentRead(AgentBase):
    """
    Pydantic model for reading AI Agent data.
    """
    
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
