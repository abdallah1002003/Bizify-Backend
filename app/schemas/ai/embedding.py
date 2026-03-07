from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class EmbeddingBase(BaseModel):
    business_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    content: str
    vector: list[float]

class EmbeddingCreate(BaseModel):
    business_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    content: str
    vector: list[float] = Field(..., min_length=1)

class EmbeddingUpdate(BaseModel):
    business_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    content: Optional[str] = None
    vector: Optional[list[float]] = None
    created_at: Optional[datetime] = None

class EmbeddingResponse(EmbeddingBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
