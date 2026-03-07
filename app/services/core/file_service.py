"""
File CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import File
from app.services.base_service import BaseService
from app.db.database import get_async_db
from app.core.crud_utils import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)

class FileService(BaseService):
    """Service for managing File records."""
    db: AsyncSession

    async def get_file(self, id: UUID) -> Optional[File]:
        """Retrieve a file by ID."""
        stmt = select(File).where(File.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_files(
        self,
        skip: int = 0,
        limit: int = 100,
        owner_id: Optional[UUID] = None,
    ) -> List[File]:
        """Retrieve multiple files with optional owner filtering."""
        stmt = select(File).offset(skip).limit(limit)
        if owner_id is not None:
            stmt = stmt.where(File.owner_id == owner_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_file(self, obj_in: Any) -> File:
        """Create a new file record."""
        db_obj = File(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_file(self, db_obj: File, obj_in: Any) -> File:
        """Update an existing file record."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_file(self, id: UUID) -> Optional[File]:
        """Delete a file record."""
        db_obj = await self.get_file(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

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
