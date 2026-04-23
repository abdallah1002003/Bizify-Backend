from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Shared CRUD helpers for SQLAlchemy-backed models."""

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Return a single record by primary key."""
        return db.get(self.model, id)

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Return a paginated list of records."""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(
        self,
        db: Session,
        *,
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
        commit: bool = True,
        refresh: bool = True,
    ) -> ModelType:
        """Create and optionally commit a new record."""
        if isinstance(obj_in, dict):
            obj_in_data = obj_in.copy()
        else:
            obj_in_data = obj_in.model_dump(mode="python")
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        if commit:
            db.commit()
        else:
            db.flush()
        if refresh:
            db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        commit: bool = True,
        refresh: bool = True,
    ) -> ModelType:
        """Update an existing record with partial data."""
        obj_data = {
            column.name: getattr(db_obj, column.name)
            for column in db_obj.__table__.columns
        }
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            update_data = obj_in.model_dump(exclude_unset=True, mode="python")

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        if commit:
            db.commit()
        else:
            db.flush()
        if refresh:
            db.refresh(db_obj)
        return db_obj

    def save(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        commit: bool = True,
        refresh: bool = True,
    ) -> ModelType:
        """Persist an already-instantiated model."""
        db.add(db_obj)
        if commit:
            db.commit()
        else:
            db.flush()
        if refresh:
            db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any, commit: bool = True) -> Optional[ModelType]:
        """Delete a record by primary key."""
        obj = db.get(self.model, id)
        if obj is None:
            return None
        db.delete(obj)
        if commit:
            db.commit()
        else:
            db.flush()
        return obj

    def delete_instance(self, db: Session, *, db_obj: ModelType, commit: bool = True) -> ModelType:
        """Delete a loaded model instance."""
        db.delete(db_obj)
        if commit:
            db.commit()
        else:
            db.flush()
        return db_obj
