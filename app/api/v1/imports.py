from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.import_service import import_service

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Upload a document, extract text, and save it."""
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded",
        )

    document = await import_service.process_and_save_document(
        db=db,
        file=file,
        current_user_id=current_user.id,
    )
    return {
        "message": "Document uploaded and processed successfully!",
        "document_id": document.id,
        "filename": document.filename,
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Delete a document belonging to the current user."""
    document = import_service.delete_document_for_user(db, document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have permission to delete it",
        )

    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/export-ai")
async def export_document_for_ai(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return extracted document text for downstream AI workflows."""
    document = import_service.get_document_for_user(db, document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return {
        "document_id": document.id,
        "filename": document.filename,
        "content_type": document.content_type,
        "extracted_text": document.extracted_text,
    }
