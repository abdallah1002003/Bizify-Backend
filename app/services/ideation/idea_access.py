import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import IdeaAccess
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


class IdeaAccessService(BaseService):
    """Service for managing access permissions to Ideas."""

    def check_idea_access(self, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
        """Check if a user has specific permissions for an idea."""
        from app.models.ideation.idea import Idea
        idea = self.db.query(Idea).filter(Idea.id == idea_id).first()
        if idea is None:
            return False

        if idea.owner_id == user_id:
            return True

        access = (
            self.db.query(IdeaAccess)
            .filter(IdeaAccess.idea_id == idea_id, IdeaAccess.user_id == user_id)
            .first()
        )
        if access is None:
            return False

        if required_perm == "view":
            return True
        if required_perm == "edit":
            return bool(access.can_edit)
        if required_perm == "delete":
            return bool(access.can_delete)
        if required_perm == "experiment":
            return bool(access.can_experiment)

        return False

    def grant_access(self, idea_id: UUID, user_id: UUID, permissions: Dict[str, bool]) -> IdeaAccess:
        """Grant or update access permissions for a user on an idea."""
        access = (
            self.db.query(IdeaAccess)
            .filter(IdeaAccess.idea_id == idea_id, IdeaAccess.user_id == user_id)
            .first()
        )
        if access is None:
            access = IdeaAccess(
                idea_id=idea_id,
                user_id=user_id,
                can_edit=permissions.get("edit", False),
                can_delete=permissions.get("delete", False),
                can_experiment=permissions.get("experiment", False),
            )
            self.db.add(access)
        else:
            access.can_edit = permissions.get("edit", access.can_edit)
            access.can_delete = permissions.get("delete", access.can_delete)
            access.can_experiment = permissions.get("experiment", access.can_experiment)

        self.db.commit()
        self.db.refresh(access)
        return access  # type: ignore[no-any-return]

    def get_idea_access(self, id: UUID) -> Optional[IdeaAccess]:
        return self.db.query(IdeaAccess).filter(IdeaAccess.id == id).first()  # type: ignore[no-any-return]

    def get_idea_accesses(self, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
        return self.db.query(IdeaAccess).offset(skip).limit(limit).all()  # type: ignore[no-any-return]

    def get_idea_accesses_by_owner(self, owner_id: UUID, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
        from app.models.ideation.idea import Idea
        return (  # type: ignore[no-any-return]
            self.db.query(IdeaAccess)
            .join(Idea, IdeaAccess.idea_id == Idea.id)
            .filter(Idea.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_idea_access(self, obj_in: Any) -> IdeaAccess:
        db_obj = IdeaAccess(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_idea_access(self, db_obj: IdeaAccess, obj_in: Any) -> IdeaAccess:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_idea_access(self, id: UUID) -> Optional[IdeaAccess]:
        db_obj = self.get_idea_access(id=id)
        if not db_obj:
            return None

        self.db.delete(db_obj)
        self.db.commit()
        return db_obj


def get_idea_access_service(db: Session = Depends(get_db)) -> IdeaAccessService:
    return IdeaAccessService(db)

# Legacy aliases
def check_idea_access(db: Session, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
    return IdeaAccessService(db).check_idea_access(idea_id, user_id, required_perm)

def grant_access(db: Session, idea_id: UUID, user_id: UUID, permissions: Dict[str, bool]) -> IdeaAccess:
    return IdeaAccessService(db).grant_access(idea_id, user_id, permissions)
