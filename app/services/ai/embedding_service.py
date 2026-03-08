from __future__ import annotations
import logging
from typing import Any, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.models import Embedding
from app.services.base_service import BaseService
from app.services.ai import provider_runtime
from app.repositories.ai_repository import EmbeddingRepository

logger = logging.getLogger(__name__)

class EmbeddingService(BaseService):
    """Service for managing AI embeddings and vectorization."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = EmbeddingRepository(db)

    async def get_embedding(self, id: UUID) -> Optional[Embedding]:
        """Retrieve a single embedding by ID."""
        return await self.repo.get(id)

    async def get_embeddings(self, skip: int = 0, limit: int = 100) -> List[Embedding]:
        """Retrieve paginated embeddings."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_embedding(self, obj_in: Any) -> Embedding:
        """Create a new embedding record."""
        return await self.repo.create(obj_in)

    async def delete_embedding(self, id: UUID) -> Optional[Embedding]:
        """Delete an embedding by ID."""
        return await self.repo.delete(id)

    async def trigger_vectorization(
        self,
        target_id: UUID,
        target_type: str,
        content: str,
        agent_id: Optional[UUID] = None,
    ) -> Optional[Embedding]:
        """Generate an embedding vector and store it."""
        if len(content) < 10:
            return None

        business_id = target_id if target_type.upper() == "BUSINESS" else None
        vector = await provider_runtime.generate_embedding_vector(content)
        return await self.create_embedding(
            {
                "business_id": business_id,
                "agent_id": agent_id,
                "content": content,
                "vector": vector,
            },
        )

async def get_embedding_service(db: AsyncSession = Depends(get_async_db)) -> EmbeddingService:
    """Dependency provider for EmbeddingService."""
    return EmbeddingService(db)
