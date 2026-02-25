from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_db
from app.schemas.core.share_link import ShareLinkCreate, ShareLinkUpdate, ShareLinkResponse
from app.services.core import share_link_service as service

router = APIRouter()


def _ensure_share_link_owner(share_link: models.ShareLink, current_user: models.User) -> None:
    if share_link.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[ShareLinkResponse])
def read_share_links(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return service.get_share_links(db, skip=skip, limit=limit, created_by=current_user.id)

@router.post("/", response_model=ShareLinkResponse)
def create_share_link(
    item_in: ShareLinkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["created_by"] = current_user.id
    return service.create_share_link(db, obj_in=data)

@router.get("/{id}", response_model=ShareLinkResponse)
def read_share_link(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_share_link(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ShareLink not found")
    _ensure_share_link_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=ShareLinkResponse)
def update_share_link(
    id: UUID,
    item_in: ShareLinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_share_link(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ShareLink not found")
    _ensure_share_link_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("created_by", None)
    return service.update_share_link(db, db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=ShareLinkResponse)
def delete_share_link(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_share_link(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ShareLink not found")
    _ensure_share_link_owner(db_obj, current_user)
    return service.delete_share_link(db, id=id)
