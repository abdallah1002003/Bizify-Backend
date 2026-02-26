"""
Base repository providing generic CRUD operations for SQLAlchemy models.

Services can optionally delegate database access to a typed repository
instance to gain a clean separation between business logic and persistence.

Usage::

    from app.repositories.base_repository import GenericRepository
    from app.models.users.user import User

    class UserRepository(GenericRepository[User]):
        pass  # inherits get, get_all, create, update, delete

    # In a service:
    repo = UserRepository(db, User)
    user = repo.get(user_id)
    users = repo.get_all(skip=0, limit=20)
"""

from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class GenericRepository(Generic[ModelType]):
    """
    Generic CRUD repository for any SQLAlchemy model (Asynchronous).

    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages.

    Args:
        db: Active SQLAlchemy AsyncSession.
        model: The SQLAlchemy model class (e.g. ``User``, ``Idea``).
    """

    def __init__(self, db: AsyncSession, model: Type[ModelType]) -> None:
        self.db = db
        self.model = model

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get(self, id: Any) -> Optional[ModelType]:
        """Retrieve a single record by primary key."""
        return cast(Optional[ModelType], await self.db.get(self.model, id))


    async def get_all(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Retrieve a paginated list of records."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return cast(List[ModelType], list(result.scalars().all()))


    async def count(self) -> int:
        """Return the total number of records in the table."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.db.execute(stmt)
        return cast(int, result.scalar())

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create and persist a new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], Any],
    ) -> ModelType:
        """Update an existing record with new field values."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        elif hasattr(obj_in, "model_dump"):
            update_data = obj_in.model_dump(exclude_unset=True)
        elif hasattr(obj_in, "dict"):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = dict(obj_in)

        for field, value in update_data.items():
            if value is not None and hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: Any) -> Optional[ModelType]:
        """Delete a record by primary key."""
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.commit()
        return obj
