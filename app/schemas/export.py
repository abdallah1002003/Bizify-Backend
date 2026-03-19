import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.export_job import ExportStatus

class ExportRequest(BaseModel):
    """
    Pydantic model for requesting a data export job.
    """

    scope: List[str] = Field(
        default=["profile", "skills", "ideas"],
        description="List of data sections to export. Allowed values: 'profile', 'skills', 'ideas'."
    )
    format: str = Field(
        default="pdf",
        description="The export format. Allowed values: 'json', 'pdf', 'word'."
    )


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
