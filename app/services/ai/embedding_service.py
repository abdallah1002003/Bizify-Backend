from __future__ import annotations
import logging
from typing import Any, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Embedding
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.services.ai import provider_runtime

logger = logging.getLogger(__name__)

class EmbeddingService(BaseService):
    """Service for managing AI embeddings and vectorization."""

    def get_embedding(self, id: UUID) -> Optional[Embedding]:
        return self.db.query(Embedding).filter(Embedding.id == id).first()

    def get_embeddings(self, skip: int = 0, limit: int = 100) -> List[Embedding]:
        return self.db.query(Embedding).offset(skip).limit(limit).all()

    def create_embedding(self, obj_in: Any) -> Embedding:
        db_obj = Embedding(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_embedding(self, id: UUID) -> Optional[Embedding]:
        db_obj = self.get_embedding(id=id)
        if not db_obj:
            return None
        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

    async def trigger_vectorization(
        self,
        target_id: UUID,
        target_type: str,
        content: str,
        agent_id: Optional[UUID] = None,
    ) -> Optional[Embedding]:
        if len(content) < 10:
            return None

        business_id = target_id if target_type.upper() == "BUSINESS" else None
        vector = await provider_runtime.generate_embedding_vector(content)
        if vector is None:
            return None

        return self.create_embedding(
            {
                "business_id": business_id,
                "agent_id": agent_id,
                "content": content,
                "vector": vector,
            },
        )

def get_embedding_service(db: Session = Depends(get_db)) -> EmbeddingService:
    return EmbeddingService(db)
