from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class EmbeddingBase(BaseModel):
    business_id: UUID
    agent_id: UUID
    content: str
    vector: Optional[str] = None

class EmbeddingCreate(EmbeddingBase):
    pass

class EmbeddingRead(EmbeddingBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
