import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmbeddingBase(BaseModel):
    """
    Base Pydantic model for Embedding data.
    """
    
    business_id: uuid.UUID
    agent_id: uuid.UUID
    content: str
    vector: Optional[str] = None


class EmbeddingCreate(EmbeddingBase):
    """
    Pydantic model for creating a new Embedding.
    """
    
    pass


class EmbeddingRead(EmbeddingBase):
    """
    Pydantic model for reading Embedding data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
