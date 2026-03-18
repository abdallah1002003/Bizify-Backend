import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.document import Document
from app.services.import_service import import_service

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint to upload documents (PDF, Word, TXT), extract text, and save to database.
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded"
        )
    
    document = await import_service.process_and_save_document(
        db=db, 
        file=file, 
        current_user_id=current_user.id
    )
    
    return {
        "message": "Document uploaded and processed successfully!",
        "document_id": document.id,
        "filename": document.filename
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint for users to delete their uploaded documents.
    """
    document = db.query(Document).filter(
        Document.id == document_id, 
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have permission to delete it"
        )
        
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/export-ai")
async def export_document_for_ai(
    document_id: uuid.UUID,  
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Special endpoint to provide the document text in JSON format for the AI Engineer 
    to use in the AI Agent.
    """
    document = db.query(Document).filter(
        Document.id == document_id, 
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
        
    
    return {
        "document_id": document.id,
        "filename": document.filename,
        "content_type": document.content_type,
        "extracted_text": document.extracted_text
    }
