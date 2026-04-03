import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import dependencies as deps
from app.models.export_job import ExportStatus
from app.models.user import User
from app.schemas.export import ExportJobResponse, ExportRequest
from app.services.export_service import ExportService


router = APIRouter()


@router.post("/", response_model = ExportJobResponse)
def request_data_export(
    *,
    db: Session = Depends(deps.get_db),
    export_in: ExportRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Start a new data export process in the background.
    """
    return ExportService.request_export(
        db = db,
        user_id = current_user.id,
        scope = export_in.scope,
        format = export_in.format
    )


@router.post("/{job_id}/cancel")
def cancel_export(
    job_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Cancel the export process and prevent Celery from completing it.
    """
    is_cancelled = ExportService.cancel_export(
        db = db,
        job_id = job_id,
        user_id = current_user.id,
    )

    if not is_cancelled:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Cannot cancel this job"
        )

    return {"message": "Export cancelled successfully"}


@router.get("/{job_id}", response_model = ExportJobResponse)
def get_export_status(
    job_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Check the status of the export process.
    """
    job = ExportService.get_job_for_user(db, job_id, current_user.id)

    if not job:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Export job not found"
        )

    return job


@router.get("/{job_id}/download")
def download_export_file(
    job_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> FileResponse:
    """
    Download the file resulting from the export process.
    """
    job = ExportService.get_job_for_user(db, job_id, current_user.id)

    if not job:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Export not found"
        )

    if job.status != ExportStatus.COMPLETED:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Export not ready yet"
        )

    if not job.storage_path or not os.path.exists(job.storage_path):
        raise HTTPException(
            status_code = status.HTTP_410_GONE,
            detail = "File no longer exists or expired"
        )

    format_type = getattr(job, "format", "pdf").lower()
    media_types = {
        "json": "application/json",
        "pdf": "application/pdf",
        "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }

    file_ext = "docx" if format_type == "word" else format_type

    return FileResponse(
        path = job.storage_path,
        filename = f"bizify_export_{job.id}.{file_ext}",
        media_type = media_types.get(format_type, "application/json")
    )
