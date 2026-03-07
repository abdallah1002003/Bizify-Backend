from __future__ import annotations
import logging
from typing import Any, List, Optional
from uuid import UUID
<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession
=======
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_async_db
>>>>>>> origin/main
from app.models import Embedding
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.services.ai import provider_runtime
<<<<<<< HEAD
from app.repositories.ai_repository import EmbeddingRepository
=======
>>>>>>> origin/main

logger = logging.getLogger(__name__)

class EmbeddingService(BaseService):
    """Service for managing AI embeddings and vectorization."""
<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
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
        return await self.repo.create(_to_update_dict(obj_in))
=======
    db: AsyncSession

    async def get_embedding(self, id: UUID) -> Optional[Embedding]:
        """Retrieve a single embedding by ID."""
        stmt = select(Embedding).where(Embedding.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_embeddings(self, skip: int = 0, limit: int = 100) -> List[Embedding]:
        """Retrieve paginated embeddings."""
        stmt = select(Embedding).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_embedding(self, obj_in: Any) -> Embedding:
        """Create a new embedding record."""
        db_obj = Embedding(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
>>>>>>> origin/main

    async def delete_embedding(self, id: UUID) -> Optional[Embedding]:
        """Delete an embedding by ID."""
        db_obj = await self.get_embedding(id=id)
<<<<<<< HEAD
        if db_obj:
            return await self.repo.delete(db_obj)
        return None
=======
        if not db_obj:
            return None
        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj
>>>>>>> origin/main

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
<<<<<<< HEAD
        ai_provider = provider_runtime.AIProviderService(self.db)
        vector = await ai_provider.generate_embedding_vector(content)
=======
        vector = await provider_runtime.generate_embedding_vector(content)
>>>>>>> origin/main
        return await self.create_embedding(
            {
                "business_id": business_id,
                "agent_id": agent_id,
                "content": content,
                "vector": vector,
            },
        )

<<<<<<< HEAD
async def get_embedding_service(db: AsyncSession) -> EmbeddingService:
=======
async def get_embedding_service(db: AsyncSession = Depends(get_async_db)) -> EmbeddingService:
>>>>>>> origin/main
    """Dependency provider for EmbeddingService."""
    return EmbeddingService(db)
