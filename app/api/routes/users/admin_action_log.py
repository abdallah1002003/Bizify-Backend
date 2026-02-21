from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.users.admin_action_log import AdminActionLogCreate, AdminActionLogUpdate, AdminActionLogResponse
from app.services.users import user_service as service
from app.core.dependencies import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])

@router.get("/", response_model=List[AdminActionLogResponse])
def read_admin_action_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_admin_action_logs(db, skip=skip, limit=limit)

@router.post("/", response_model=AdminActionLogResponse)
def create_admin_action_log(item_in: AdminActionLogCreate, db: Session = Depends(get_db)):
    return service.create_admin_action_log(db, obj_in=item_in)

@router.get("/{id}", response_model=AdminActionLogResponse)
def read_admin_action_log(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_admin_action_log(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AdminActionLog not found")
    return db_obj

@router.put("/{id}", response_model=AdminActionLogResponse)
def update_admin_action_log(id: UUID, item_in: AdminActionLogUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_admin_action_log(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AdminActionLog not found")
    return service.update_admin_action_log(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=AdminActionLogResponse)
def delete_admin_action_log(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_admin_action_log(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="AdminActionLog not found")
    return service.delete_admin_action_log(db, id=id)
