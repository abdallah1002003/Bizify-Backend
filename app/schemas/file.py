from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class FileBase(BaseModel):
    owner_id: UUID
    file_path: str
    file_type: Optional[str] = None
    size: Optional[int] = None

class FileRead(FileBase):
    id: UUID
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)
