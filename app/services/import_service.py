import io
import csv
import uuid
import docx
import pypdf
from pptx import Presentation
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.document_repo import document_repo

class ImportService:
    
    async def process_and_save_document(self, db: Session, file: UploadFile, current_user_id: uuid.UUID) -> Document:
        """
        Reads the uploaded file, extracts text based on its format (PDF, DOCX, TXT, CSV, PPTX),
        and saves it to the database.
        """
        file_bytes = await file.read()
        extracted_text = ""
        
        try:
            content_type = file.content_type
            filename = file.filename.lower()

            # PDF
            if content_type == "application/pdf" or filename.endswith(".pdf"):
                extracted_text = self._extract_text_from_pdf(file_bytes)
                
            # Word (DOCX)
            elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"] or filename.endswith(".docx"):
                extracted_text = self._extract_text_from_docx(file_bytes)
            
            # PowerPoint (PPTX)
            elif content_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation" or filename.endswith(".pptx"):
                extracted_text = self._extract_text_from_pptx(file_bytes)
            
            # CSV
            elif content_type == "text/csv" or filename.endswith(".csv"):
                extracted_text = self._extract_text_from_csv(file_bytes)
                
            # Plain Text (TXT)
            elif content_type == "text/plain" or filename.endswith(".txt"):
                extracted_text = file_bytes.decode("utf-8")
                
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file format. Supported: PDF, DOCX, PPTX, CSV, TXT."
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error extracting text from document: {str(e)}"
            )

        new_document = document_repo.create(db, obj_in={
            "filename": file.filename,
            "content_type": file.content_type or "text/plain",
            "extracted_text": extracted_text.strip(),
            "user_id": current_user_id
        })
        
        return new_document

    def get_document_for_user(
        self,
        db: Session,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Document | None:
        return document_repo.get_for_user(db, document_id, user_id)

    def delete_document_for_user(
        self,
        db: Session,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Document | None:
        document = self.get_document_for_user(db, document_id, user_id)
        if not document:
            return None
        document_repo.delete_instance(db, db_obj=document)
        return document

    def _extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Helper method to extract text from a PDF file."""
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text_pages = []
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_pages.append(page_text)
        return "\n".join(text_pages)

    def _extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Helper method to extract text from a Word (docx) file."""
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text

    def _extract_text_from_pptx(self, file_bytes: bytes) -> str:
        """Helper method to extract text from a PowerPoint (pptx) file."""
        prs = Presentation(io.BytesIO(file_bytes))
        text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
        return "\n".join(text)

    def _extract_text_from_csv(self, file_bytes: bytes) -> str:
        """Helper method to extract text from a CSV file."""
        content = file_bytes.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        text = []
        for row in reader:
            text.append(" ".join(row))
        return "\n".join(text)

import_service = ImportService()
