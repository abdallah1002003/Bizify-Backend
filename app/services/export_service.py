import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

from docx import Document
from fpdf import FPDF

from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.export_job import ExportJob, ExportStatus
from app.models.idea import Idea
from app.models.user_profile import UserProfile
from app.models.user_skill import UserSkill


def _sanitize_for_fpdf(text: str) -> str:
    """Replaces non-latin1 characters with '?' to prevent FPDF2 crashes with default fonts."""
    if not text: return ""
    text_str = str(text)
    return "".join(c if ord(c) < 256 else "?" for c in text_str)

def _generate_docx(data: dict, file_path: str) -> None:
    doc = Document()
    doc.add_heading('Bizify Data Export', 0)
    
    if "profile" in data:
        doc.add_heading('Profile Info', level=1)
        prof = data["profile"]
        doc.add_paragraph(f"Bio: {prof.get('bio', '')}")
        doc.add_paragraph(f"Interests: {json.dumps(prof.get('interests', []), ensure_ascii=False)}")
        doc.add_paragraph(f"Background: {json.dumps(prof.get('background', {}), ensure_ascii=False)}")
        
    if "skills" in data:
        doc.add_heading('Skills', level=1)
        for skill in data["skills"]:
            doc.add_paragraph(f"- {skill['name']} (Level: {skill['level']})")
            
    if "ideas" in data:
        doc.add_heading('Ideas', level=1)
        for idea in data["ideas"]:
            doc.add_heading(idea.get("title", "Untitled"), level=2)
            doc.add_paragraph(f"Status: {idea.get('status', '')}")
            doc.add_paragraph(str(idea.get("description", "")))
            
    doc.save(file_path)

def _generate_pdf(data: dict, file_path: str) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    pdf.set_font("helvetica", "B", 15)
    pdf.cell(0, 10, _sanitize_for_fpdf("Bizify Data Export"), border=False, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    if "profile" in data:
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Profile Info", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=11)
        prof = data["profile"]
        bio = _sanitize_for_fpdf(f"Bio: {prof.get('bio', '')}")
        interests = _sanitize_for_fpdf(f"Interests: {json.dumps(prof.get('interests', []))}")
        background = _sanitize_for_fpdf(f"Background: {json.dumps(prof.get('background', {}))}")
        pdf.multi_cell(0, 8, f"{bio}\n{interests}\n{background}")
        pdf.ln(5)
        
    if "skills" in data:
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Skills", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=11)
        for skill in data["skills"]:
            item = _sanitize_for_fpdf(f"- {skill['name']} (Level: {skill['level']})")
            pdf.cell(0, 8, item, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
            
    if "ideas" in data:
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Ideas", new_x="LMARGIN", new_y="NEXT")
        for idea in data["ideas"]:
            pdf.set_font("helvetica", "B", 12)
            title = _sanitize_for_fpdf(idea.get("title", "Untitled"))
            pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "I", 10)
            status = _sanitize_for_fpdf(f"Status: {idea.get('status', '')}")
            pdf.cell(0, 6, status, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", size=11)
            desc = _sanitize_for_fpdf(str(idea.get("description", "")))
            pdf.multi_cell(0, 6, desc)
            pdf.ln(4)
            
    pdf.output(file_path)

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
        
        format_type = getattr(job, "format", "pdf").lower()
        file_ext = "docx" if format_type == "word" else format_type
        file_name = f"export_{job.id}.{file_ext}"
        file_path = os.path.join(storage_dir, file_name)

        if format_type == "word":
            _generate_docx(data_to_export, file_path)
        elif format_type == "pdf":
            _generate_pdf(data_to_export, file_path)
        else:
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
