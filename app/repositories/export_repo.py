import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.export_job import ExportJob, ExportStatus
from app.repositories.base import BaseRepository


class ExportRepository(BaseRepository[ExportJob, Any, Any]):
    """
    Repository for ExportJob database operations.
    """

    def get_by_id(self, db: Session, job_id: uuid.UUID) -> Optional[ExportJob]:
        """Fetch an export job record by its ID."""
        return db.query(self.model).filter(self.model.id == job_id).first()

    def get_for_user(
        self,
        db: Session,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[ExportJob]:
        return (
            db.query(self.model)
            .filter(
                self.model.id == job_id,
                self.model.user_id == user_id,
            )
            .first()
        )

    def update_status(
        self,
        db: Session,
        job: ExportJob,
        status: ExportStatus,
        file_path: Optional[str] = None,
        commit: bool = True,
    ) -> ExportJob:
        """
        Update the lifecycle status of an export job.
        Optionally saves the generated file path when the job completes.
        """
        job.status = status
        if file_path:
            job.storage_path = file_path
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(job)
        return job


export_repo = ExportRepository(ExportJob)
