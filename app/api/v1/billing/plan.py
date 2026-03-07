from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam, PageResponse
from app.core.dependencies import get_current_active_user, require_admin
import app.models as models
from app.schemas.billing.plan import PlanCreate, PlanUpdate, PlanResponse
<<<<<<< HEAD
from app.services.billing.plan_service import PlanService
from app.api.v1.service_dependencies import get_plan_service
=======
from app.services.billing.plan_service import PlanService, get_plan_service
>>>>>>> origin/main

router = APIRouter()


@router.get("/", response_model=PageResponse[PlanResponse])
async def read_plans(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    service: PlanService = Depends(get_plan_service),
    current_user: models.User = Depends(get_current_active_user),
):
    """List all billing plans with pagination. Accessible to all authenticated users."""
    _ = current_user
    total = await service.count_plans()
    items = await service.get_plans(skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/", response_model=PlanResponse, dependencies=[Depends(require_admin)])
async def create_plan(
    item_in: PlanCreate,
    service: PlanService = Depends(get_plan_service),
):
    return await service.create_plan(obj_in=item_in)


@router.get("/{id}", response_model=PlanResponse)
async def read_plan(
    id: UUID,
    service: PlanService = Depends(get_plan_service),
    current_user: models.User = Depends(get_current_active_user),
):
    _ = current_user
    db_obj = await service.get_plan(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db_obj


@router.put("/{id}", response_model=PlanResponse, dependencies=[Depends(require_admin)])
async def update_plan(
    id: UUID,
    item_in: PlanUpdate,
    service: PlanService = Depends(get_plan_service),
):
    db_obj = await service.get_plan(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return await service.update_plan(db_obj=db_obj, obj_in=item_in)


@router.delete("/{id}", response_model=PlanResponse, dependencies=[Depends(require_admin)])
async def delete_plan(
    id: UUID,
    service: PlanService = Depends(get_plan_service),
):
    db_obj = await service.get_plan(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return await service.delete_plan(id=id)
