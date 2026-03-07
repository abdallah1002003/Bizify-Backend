from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.schemas.ai.embedding import EmbeddingCreate, EmbeddingUpdate, EmbeddingResponse
from app.services.ai import ai_service as service

router = APIRouter()

@router.get("/", response_model=List[EmbeddingResponse])
async def read_embeddings(skip: SkipParam = 0, limit: LimitParam = 100, db: AsyncSession = Depends(get_async_db)):
    return await service.get_embeddings(db, skip=skip, limit=limit)

@router.post("/", response_model=EmbeddingResponse)
async def create_embedding(item_in: EmbeddingCreate, db: AsyncSession = Depends(get_async_db)):
    return await service.create_embedding(db, obj_in=item_in)

@router.get("/{id}", response_model=EmbeddingResponse)
async def read_embedding(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_embedding(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return db_obj

@router.put("/{id}", response_model=EmbeddingResponse)
async def update_embedding(id: UUID, item_in: EmbeddingUpdate, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_embedding(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return await service.update_embedding(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=EmbeddingResponse)
async def delete_embedding(id: UUID, db: AsyncSession = Depends(get_async_db)):
    db_obj = await service.get_embedding(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return await service.delete_embedding(db, id=id)
