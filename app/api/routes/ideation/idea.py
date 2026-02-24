from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ideation.idea import IdeaCreate, IdeaUpdate, IdeaResponse
from app.services.ideation.idea_service import IdeaService, get_idea_service
from app.core.dependencies import get_current_active_user
import app.models as models

router = APIRouter()

@router.get("/", response_model=List[IdeaResponse])
def read_ideas(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """List ideas visible to current user with pagination."""
    return service.get_ideas(skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=IdeaResponse)
def create_idea(
    item_in: IdeaCreate, 
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elite API: Secure idea creation with auto-versioning."""
    item_in.owner_id = current_user.id or item_in.owner_id
    return service.create_idea(obj_in=item_in)

@router.get("/{id}", response_model=IdeaResponse)
def read_idea(
    id: UUID, 
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elite API: RBAC-verified retrieval."""
    db_obj = service.get_idea(id=id, user_id=current_user.id)
    if not db_obj: 
        raise HTTPException(status_code=404, detail="Idea not found")
    return db_obj

@router.put("/{id}", response_model=IdeaResponse)
def update_idea(
    id: UUID, 
    item_in: IdeaUpdate, 
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elite API: Protected mutation with lineage tracking."""
    db_obj = service.get_idea(id=id)
    if not db_obj:
         raise HTTPException(status_code=404, detail="Idea not found")
    return service.update_idea(db_obj=db_obj, obj_in=item_in, performer_id=current_user.id)

@router.delete("/{id}", response_model=IdeaResponse)
def delete_idea(
    id: UUID, 
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elite API: Secure deletion with ownership verification."""
    if not service.check_idea_access(id, current_user.id, "delete"):
        raise HTTPException(status_code=403, detail="Ownership required for deletion")
    return service.delete_idea(id=id)
