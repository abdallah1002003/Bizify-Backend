from __future__ import annotations
import logging
from typing import Any, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.models import File
from app.services.base_service import BaseService
from app.repositories.core_repository import FileRepository

logger = logging.getLogger(__name__)

class FileService(BaseService):
    """Service for managing File records."""
    
    def __init__(self, db: AsyncSession):
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
        return await self.repo.create(obj_in)

    async def update_file(self, db_obj: File, obj_in: Any) -> File:
        """Update an existing file record."""
        return await self.repo.update(db_obj, obj_in)

    async def delete_file(self, id: UUID) -> Optional[File]:
        """Delete a file record."""
        return await self.repo.delete(id)

async def get_file_service(db: AsyncSession = Depends(get_async_db)) -> FileService:
    """Dependency provider for FileService."""
    return FileService(db)

# ----------------------------
# Legacy Async Aliases
# ----------------------------

async def get_file(db: AsyncSession, id: UUID) -> Optional[File]:
    """Legacy async alias for getting a file."""
    return await FileService(db).get_file(id)

async def get_files(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[UUID] = None,
) -> List[File]:
    """Legacy async alias for getting multiple files."""
    return await FileService(db).get_files(skip, limit, owner_id)

async def create_file(db: AsyncSession, obj_in: Any) -> File:
    """Legacy async alias for creating a file."""
    return await FileService(db).create_file(obj_in)

async def update_file(db: AsyncSession, db_obj: File, obj_in: Any) -> File:
    """Legacy async alias for updating a file."""
    return await FileService(db).update_file(db_obj, obj_in)

async def delete_file(db: AsyncSession, id: UUID) -> Optional[File]:
    """Legacy async alias for deleting a file."""
    return await FileService(db).delete_file(id)

# Backward compatibility alias
create_file_record = create_file
