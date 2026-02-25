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

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class GenericRepository(Generic[ModelType]):
    """
    Generic CRUD repository for any SQLAlchemy model.

    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages.

    Args:
        db: Active SQLAlchemy session (injected via FastAPI Depends).
        model: The SQLAlchemy model class (e.g. ``User``, ``Idea``).

    Example::

        class IdeaRepository(GenericRepository[Idea]):
            def get_by_owner(self, owner_id) -> List[Idea]:
                return self.db.query(self.model).filter(
                    self.model.owner_id == owner_id
                ).all()
    """

    def __init__(self, db: Session, model: Type[ModelType]) -> None:
        self.db = db
        self.model = model

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, id: Any) -> Optional[ModelType]:
        """
        Retrieve a single record by primary key.

        Args:
            id: Primary key value of the record.

        Returns:
            The model instance, or None if not found.
        """
        return self.db.get(self.model, id)

    def get_all(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Retrieve a paginated list of records.

        Args:
            skip: Number of records to skip (offset). Defaults to 0.
            limit: Maximum number of records to return. Defaults to 100.

        Returns:
            List of model instances.
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def count(self) -> int:
        """Return the total number of records in the table."""
        return self.db.query(self.model).count()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        Create and persist a new record.

        Args:
            obj_in: Dictionary of field name → value. Keys must match
                    column names on the model.

        Returns:
            The newly created and refreshed model instance.
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], Any],
    ) -> ModelType:
        """
        Update an existing record with new field values.

        Accepts either a plain ``dict`` or a Pydantic model (anything with
        a ``model_dump`` / ``dict`` method, or iterable key-value pairs).

        Args:
            db_obj: Existing model instance to update (loaded from DB).
            obj_in: New values. Non-None values overwrite existing attributes.

        Returns:
            The updated and refreshed model instance.
        """
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
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: Any) -> Optional[ModelType]:
        """
        Delete a record by primary key.

        Args:
            id: Primary key value of the record to delete.

        Returns:
            The deleted model instance, or None if not found.
        """
        obj = self.db.get(self.model, id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj
