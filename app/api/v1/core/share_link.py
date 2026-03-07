from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
import app.models as models
from app.api.v1.service_dependencies import get_share_link_service
from app.core.dependencies import get_current_active_user
from app.schemas.core.share_link import ShareLinkCreate, ShareLinkUpdate, ShareLinkResponse
from app.services.core.share_link_service import ShareLinkService

router = APIRouter()


def _ensure_share_link_owner(share_link: models.ShareLink, current_user: models.User) -> None:
    if share_link.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[ShareLinkResponse])
async def read_share_links(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: ShareLinkService = Depends(get_share_link_service),
    current_user: models.User = Depends(get_current_active_user),
):
    return await service.get_share_links(skip=skip, limit=limit, created_by=current_user.id)

@router.post("/", response_model=ShareLinkResponse)
async def create_share_link(
    item_in: ShareLinkCreate,
    service: ShareLinkService = Depends(get_share_link_service),
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["created_by"] = current_user.id
    return await service.create_share_link(obj_in=data)

@router.get("/{id}", response_model=ShareLinkResponse)
async def read_share_link(
    id: UUID,
    service: ShareLinkService = Depends(get_share_link_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_share_link(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ShareLink not found")
    _ensure_share_link_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=ShareLinkResponse)
async def update_share_link(
    id: UUID,
    item_in: ShareLinkUpdate,
    service: ShareLinkService = Depends(get_share_link_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_share_link(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ShareLink not found")
    _ensure_share_link_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("created_by", None)
    return await service.update_share_link(db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=ShareLinkResponse)
async def delete_share_link(
    id: UUID,
    service: ShareLinkService = Depends(get_share_link_service),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_share_link(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="ShareLink not found")
    _ensure_share_link_owner(db_obj, current_user)
    return await service.delete_share_link(id=id)
