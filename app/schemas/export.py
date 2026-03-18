import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.export_job import ExportStatus


class ExportRequest(BaseModel):
    """
    Pydantic model for requesting a data export job.
    """

    scope: List[str]
    format: str = "json"


class ExportJobResponse(BaseModel):
    """
    Pydantic model for reading the status of a data export job.
    """

    id: uuid.UUID
    status: ExportStatus
    scope: List[str]
    format: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes = True)
