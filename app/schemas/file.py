import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FileBase(BaseModel):
    """
    Base Pydantic model for File data.
    """
    
    owner_id: uuid.UUID
    file_path: str
    file_type: Optional[str] = None
    size: Optional[int] = None


class FileRead(FileBase):
    """
    Pydantic model for reading File data.
    """
    
    id: uuid.UUID
    uploaded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
