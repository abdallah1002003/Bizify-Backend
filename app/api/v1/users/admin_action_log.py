from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.users.admin_action_log import AdminActionLogCreate, AdminActionLogUpdate, AdminActionLogResponse
from app.services.users.user_service import UserService, get_user_service
from app.core.dependencies import require_admin

# All routes in this router require ADMIN role — enforced at the router level
router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", response_model=List[AdminActionLogResponse])
def read_admin_action_logs(  # type: ignore
    skip: SkipParam = 0, 
    limit: LimitParam = 100, 
    service: UserService = Depends(get_user_service)
):
    return service.get_admin_action_logs(skip=skip, limit=limit)


@router.post("/", response_model=AdminActionLogResponse)
def create_admin_action_log(  # type: ignore
    item_in: AdminActionLogCreate, 
    service: UserService = Depends(get_user_service)
):
    return service.create_admin_action_log(obj_in=item_in)


@router.get("/{id}", response_model=AdminActionLogResponse)
def read_admin_action_log(  # type: ignore
    id: UUID, 
    service: UserService = Depends(get_user_service)
):
    db_obj = service.get_admin_action_log(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AdminActionLog not found")
    return db_obj


@router.put("/{id}", response_model=AdminActionLogResponse)
def update_admin_action_log(  # type: ignore
    id: UUID, 
    item_in: AdminActionLogUpdate, 
    service: UserService = Depends(get_user_service)
):
    db_obj = service.get_admin_action_log(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AdminActionLog not found")
    return service.update_admin_action_log(db_obj=db_obj, obj_in=item_in)


@router.delete("/{id}", response_model=AdminActionLogResponse)
def delete_admin_action_log(  # type: ignore
    id: UUID, 
    service: UserService = Depends(get_user_service)
):
    db_obj = service.get_admin_action_log(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AdminActionLog not found")
    return service.delete_admin_action_log(id=id)
