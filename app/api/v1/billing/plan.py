from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam, PageResponse
from app.core.dependencies import get_current_active_user, require_admin
import app.models as models
from app.models.billing.billing import Plan
from app.schemas.billing.plan import PlanCreate, PlanUpdate, PlanResponse
from app.services.billing.plan_service import PlanService, get_plan_service

router = APIRouter()


@router.get("/", response_model=PageResponse[PlanResponse])
def read_plans(  # type: ignore
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    service: PlanService = Depends(get_plan_service),
    current_user: models.User = Depends(get_current_active_user),
):
    """List all billing plans with pagination. Accessible to all authenticated users."""
    _ = current_user
    total = service.db.query(Plan).count()
    items = service.get_plans(skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/", response_model=PlanResponse, dependencies=[Depends(require_admin)])
def create_plan(  # type: ignore
    item_in: PlanCreate,
    service: PlanService = Depends(get_plan_service),
):
    return service.create_plan(obj_in=item_in)


@router.get("/{id}", response_model=PlanResponse)
def read_plan(  # type: ignore
    id: UUID,
    service: PlanService = Depends(get_plan_service),
    current_user: models.User = Depends(get_current_active_user),
):
    _ = current_user
    db_obj = service.get_plan(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db_obj


@router.put("/{id}", response_model=PlanResponse, dependencies=[Depends(require_admin)])
def update_plan(  # type: ignore
    id: UUID,
    item_in: PlanUpdate,
    service: PlanService = Depends(get_plan_service),
):
    db_obj = service.get_plan(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return service.update_plan(db_obj=db_obj, obj_in=item_in)


@router.get("/{id}", response_model=PlanResponse)
@router.delete("/{id}", response_model=PlanResponse, dependencies=[Depends(require_admin)])
def delete_plan(  # type: ignore
    id: UUID,
    service: PlanService = Depends(get_plan_service),
):
    db_obj = service.get_plan(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    return service.delete_plan(id=id)
