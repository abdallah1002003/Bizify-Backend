from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.ext.asyncio import AsyncSession
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_async_db
from app.schemas.core.file import FileCreate, FileUpdate, FileResponse
from app.services.core import core_service as service

router = APIRouter()


def _ensure_file_owner(file_obj: models.File, current_user: models.User) -> None:
    if file_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[FileResponse])
async def read_files(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return await service.get_files(db, skip=skip, limit=limit, owner_id=current_user.id)

@router.post("/", response_model=FileResponse)
async def create_file(
    item_in: FileCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["owner_id"] = current_user.id
    return await service.create_file(db, obj_in=data)

@router.get("/{id}", response_model=FileResponse)
async def read_file(
    id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_file(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="File not found")
    _ensure_file_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=FileResponse)
async def update_file(
    id: UUID,
    item_in: FileUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_file(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="File not found")
    _ensure_file_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("owner_id", None)
    return await service.update_file(db, db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=FileResponse)
async def delete_file(
    id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_file(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="File not found")
    _ensure_file_owner(db_obj, current_user)
    return await service.delete_file(db, id=id)
