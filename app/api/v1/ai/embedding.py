from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.api.v1.service_dependencies import get_ai_service
from app.schemas.ai.embedding import EmbeddingCreate, EmbeddingUpdate, EmbeddingResponse
from app.services.ai.ai_service import AIService

router = APIRouter()

@router.get("/", response_model=List[EmbeddingResponse])
async def read_embeddings(
    skip: SkipParam = 0,
    limit: LimitParam = 100,
    service: AIService = Depends(get_ai_service),
):
    return await service.get_embeddings(skip=skip, limit=limit)

@router.post("/", response_model=EmbeddingResponse)
async def create_embedding(
    item_in: EmbeddingCreate,
    service: AIService = Depends(get_ai_service),
):
    return await service.create_embedding(obj_in=item_in)

@router.get("/{id}", response_model=EmbeddingResponse)
async def read_embedding(
    id: UUID,
    service: AIService = Depends(get_ai_service),
):
    db_obj = await service.get_embedding(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return db_obj

@router.put("/{id}", response_model=EmbeddingResponse)
async def update_embedding(
    id: UUID,
    item_in: EmbeddingUpdate,
    service: AIService = Depends(get_ai_service),
):
    db_obj = await service.get_embedding(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return await service.update_embedding(db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=EmbeddingResponse)
async def delete_embedding(
    id: UUID,
    service: AIService = Depends(get_ai_service),
):
    db_obj = await service.get_embedding(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return await service.delete_embedding(id=id)
