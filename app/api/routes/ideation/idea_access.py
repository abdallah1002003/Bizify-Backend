from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ideation.idea_access import IdeaAccessCreate, IdeaAccessUpdate, IdeaAccessResponse
from app.services.ideation import idea_access as service
from app.core.dependencies import get_current_active_user
import app.models as models

router = APIRouter()

def _require_idea_owner(db: Session, idea_id: UUID, current_user_id: UUID) -> None:
    from app.services.ideation.idea import get_idea
    idea = get_idea(db, id=idea_id)
    if not idea or idea.owner_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this idea")


@router.get("/", response_model=List[IdeaAccessResponse])
def read_idea_accesses(
    skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)
):
    # Returns only idea accesses for ideas owned by the current user
    return service.get_idea_accesses_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)

@router.post("/", response_model=IdeaAccessResponse)
def create_idea_access(
    item_in: IdeaAccessCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)
):
    _require_idea_owner(db, item_in.idea_id, current_user.id)
    return service.create_idea_access(db, obj_in=item_in)

@router.get("/{id}", response_model=IdeaAccessResponse)
def read_idea_access(
    id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)
):
    db_obj = service.get_idea_access(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaAccess not found")
    _require_idea_owner(db, db_obj.idea_id, current_user.id)
    return db_obj

@router.put("/{id}", response_model=IdeaAccessResponse)
def update_idea_access(
    id: UUID, item_in: IdeaAccessUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)
):
    db_obj = service.get_idea_access(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaAccess not found")
    _require_idea_owner(db, db_obj.idea_id, current_user.id)
    if item_in.idea_id and item_in.idea_id != db_obj.idea_id:
        _require_idea_owner(db, item_in.idea_id, current_user.id)
    return service.update_idea_access(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=IdeaAccessResponse)
def delete_idea_access(
    id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)
):
    db_obj = service.get_idea_access(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaAccess not found")
    _require_idea_owner(db, db_obj.idea_id, current_user.id)
    return service.delete_idea_access(db, id=id)

