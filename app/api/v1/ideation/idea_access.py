from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.ideation.idea_access import IdeaAccessCreate, IdeaAccessUpdate, IdeaAccessResponse
<<<<<<< HEAD
from app.services.ideation.idea_access import IdeaAccessService
from app.services.ideation.idea_service import IdeaService
from app.api.v1.service_dependencies import get_idea_access_service, get_idea_service
=======
from app.services.ideation.idea_access import IdeaAccessService, get_idea_access_service
from app.services.ideation.idea_service import IdeaService, get_idea_service
>>>>>>> origin/main
from app.core.dependencies import get_current_active_user
import app.models as models

router = APIRouter()

async def _require_idea_owner(idea_service: IdeaService, idea_id: UUID, current_user_id: UUID) -> None:
    idea = await idea_service.get_idea(id=idea_id)
    if not idea or idea.owner_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this idea")


@router.get("/", response_model=List[IdeaAccessResponse])
async def read_idea_accesses(
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: IdeaAccessService = Depends(get_idea_access_service), 
    current_user: models.User = Depends(get_current_active_user)
):
    # Returns only idea accesses for ideas owned by the current user
    return await service.get_idea_accesses_by_owner(owner_id=current_user.id, skip=skip, limit=limit)

@router.post("/", response_model=IdeaAccessResponse)
async def create_idea_access(
    item_in: IdeaAccessCreate, 
    service: IdeaAccessService = Depends(get_idea_access_service),
    idea_service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    await _require_idea_owner(idea_service, item_in.idea_id, current_user.id)
    return await service.create_idea_access(obj_in=item_in)

@router.get("/{id}", response_model=IdeaAccessResponse)
async def read_idea_access(
    id: UUID, 
    service: IdeaAccessService = Depends(get_idea_access_service),
    idea_service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    db_obj = await service.get_idea_access(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaAccess not found")
    await _require_idea_owner(idea_service, db_obj.idea_id, current_user.id)
    return db_obj

@router.put("/{id}", response_model=IdeaAccessResponse)
async def update_idea_access(
    id: UUID, 
    item_in: IdeaAccessUpdate, 
    service: IdeaAccessService = Depends(get_idea_access_service),
    idea_service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    db_obj = await service.get_idea_access(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaAccess not found")
    await _require_idea_owner(idea_service, db_obj.idea_id, current_user.id)
    if item_in.idea_id and item_in.idea_id != db_obj.idea_id:
        await _require_idea_owner(idea_service, item_in.idea_id, current_user.id)
    return await service.update_idea_access(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=IdeaAccessResponse)
async def delete_idea_access(
    id: UUID, 
    service: IdeaAccessService = Depends(get_idea_access_service),
    idea_service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    db_obj = await service.get_idea_access(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="IdeaAccess not found")
    await _require_idea_owner(idea_service, db_obj.idea_id, current_user.id)
    return await service.delete_idea_access(id=id)
<<<<<<< HEAD
=======

>>>>>>> origin/main
