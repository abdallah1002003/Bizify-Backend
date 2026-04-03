import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document, Any, Any]):
    """
    Repository for Document database operations.
    Used for tracking imported documents.
    """

    def get_for_user(
        self,
        db: Session,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Document]:
        return (
            db.query(self.model)
            .filter(
                self.model.id == document_id,
                self.model.user_id == user_id,
            )
            .first()
        )

document_repo = DocumentRepository(Document)
