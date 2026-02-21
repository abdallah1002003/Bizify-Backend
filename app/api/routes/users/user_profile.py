from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.users.user_profile import UserProfileCreate, UserProfileUpdate, UserProfileResponse
from app.services.users import user_service as service
from app.core.dependencies import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])

@router.get("/", response_model=List[UserProfileResponse])
def read_user_profiles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_user_profiles(db, skip=skip, limit=limit)

@router.post("/", response_model=UserProfileResponse)
def create_user_profile(item_in: UserProfileCreate, db: Session = Depends(get_db)):
    return service.create_user_profile(db, obj_in=item_in)

@router.get("/{id}", response_model=UserProfileResponse)
def read_user_profile(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_user_profile(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="UserProfile not found")
    return db_obj

@router.put("/{id}", response_model=UserProfileResponse)
def update_user_profile(id: UUID, item_in: UserProfileUpdate, db: Session = Depends(get_db)):
    db_obj = service.get_user_profile(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="UserProfile not found")
    return service.update_user_profile(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=UserProfileResponse)
def delete_user_profile(id: UUID, db: Session = Depends(get_db)):
    db_obj = service.get_user_profile(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="UserProfile not found")
    return service.delete_user_profile(db, id=id)
