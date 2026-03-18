import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.export_job import ExportJob, ExportStatus
from app.models.idea import Idea
from app.models.user_profile import UserProfile
from app.models.user_skill import UserSkill


class ExportService:
    """
    Service class for managing user data export jobs.
    Delegates heavy data collection to a Celery background task.
    """

    @staticmethod
    def request_export(
        db: Session,
        user_id: uuid.UUID,
        scope: List[str],
        format: str
    ) -> ExportJob:
        """
        Creates a new export job and dispatches it to the background task queue.
        """
        job = ExportJob(
            user_id = user_id,
            scope = scope,
            format = format,
            status = ExportStatus.PENDING
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        task = process_export_task.delay(str(job.id))

        # Store the task ID to allow cancellation later
        job.task_id = task.id
        db.commit()

        return job

    @staticmethod
    def cancel_export(db: Session, job_id: uuid.UUID) -> bool:
        """
        Cancels a pending or in-progress export job via Celery task revocation.
        """
        job = db.query(ExportJob).filter(ExportJob.id == job_id).first()

        if job and job.status in [ExportStatus.PENDING, ExportStatus.PROCESSING]:
            celery_app.control.revoke(job.task_id, terminate = True)
            job.status = ExportStatus.CANCELLED
            db.commit()
            return True

        return False


@celery_app.task(name = "app.services.export_service.process_export_task")
def process_export_task(job_id: str) -> None:
    """
    Background Celery task that collects user data and writes it to a JSON file.
    """
    db = SessionLocal()

    try:
        job = db.query(ExportJob).filter(ExportJob.id == job_id).first()

        if not job:
            return

        job.status = ExportStatus.PROCESSING
        db.commit()

        data_to_export: Dict[str, Any] = {}
        user_id = job.user_id

        if "profile" in job.scope:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile:
                data_to_export["profile"] = {
                    "bio": profile.bio,
                    "interests": profile.interests_json,
                    "background": profile.background_json
                }

        if "skills" in job.scope:
            skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
            data_to_export["skills"] = [
                {"name": s.skill_name, "level": s.declared_level} for s in skills
            ]

        if "ideas" in job.scope:
            ideas = db.query(Idea).filter(Idea.owner_id == user_id).all()
            data_to_export["ideas"] = [
                {"title": i.title, "description": i.description, "status": i.status}
                for i in ideas
            ]

        storage_dir = "storage/exports"
        os.makedirs(storage_dir, exist_ok = True)
        file_name = f"export_{job.id}.json"
        file_path = os.path.join(storage_dir, file_name)

        with open(file_path, "w", encoding = "utf-8") as f:
            json.dump(data_to_export, f, ensure_ascii = False, indent = 4)

        job.status = ExportStatus.COMPLETED
        job.storage_path = file_path
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        if job:
            job.status = ExportStatus.FAILED
            job.error_details = {"error": str(e)}
            db.commit()
    finally:
        db.close()
