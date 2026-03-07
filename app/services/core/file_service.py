"""
File CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import File
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.repositories.core_repository import FileRepository

logger = logging.getLogger(__name__)

class FileService(BaseService):
    """Service for managing File records."""
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = FileRepository(db)

    async def get_file(self, id: UUID) -> Optional[File]:
        """Retrieve a file by ID."""
        return await self.repo.get(id)

    async def get_files(
        self,
        skip: int = 0,
        limit: int = 100,
        owner_id: Optional[UUID] = None,
    ) -> List[File]:
        """Retrieve multiple files with optional owner filtering."""
        if owner_id is not None:
            return await self.repo.get_for_owner(owner_id, skip=skip, limit=limit)
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_file(self, obj_in: Any) -> File:
        """Create a new file record."""
        return await self.repo.create(_to_update_dict(obj_in))

    async def update_file(self, db_obj: File, obj_in: Any) -> File:
        """Update an existing file record."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_file(self, id: UUID) -> Optional[File]:
        """Delete a file record."""
        db_obj = await self.get_file(id=id)
        if db_obj:
            return await self.repo.delete(db_obj)
        return None

async def get_file_service(db: AsyncSession) -> FileService:
    """Dependency provider for FileService."""
    return FileService(db)
