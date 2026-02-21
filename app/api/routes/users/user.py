from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.users.user import UserCreate, UserUpdate, UserResponse
from app.services.users import user_service as service
from app.core.dependencies import get_current_active_user
import app.models as models

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _ = current_user
    return service.get_users(db, skip=skip, limit=limit)

@router.post("/", response_model=UserResponse)
def create_user(item_in: UserCreate, db: Session = Depends(get_db)):
    return service.create_user(db, obj_in=item_in)

@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: models.User = Depends(get_current_active_user),
):
    return current_user

@router.get("/{id}", response_model=UserResponse)
def read_user(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _ = current_user
    db_obj = service.get_user(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return db_obj

@router.put("/{id}", response_model=UserResponse)
def update_user(
    id: UUID,
    item_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _ = current_user
    db_obj = service.get_user(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return service.update_user(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=UserResponse)
def delete_user(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    _ = current_user
    db_obj = service.get_user(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return service.delete_user(db, id=id)
