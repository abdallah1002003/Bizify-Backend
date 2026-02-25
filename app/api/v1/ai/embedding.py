from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ai.embedding import EmbeddingCreate, EmbeddingUpdate, EmbeddingResponse
from app.services.ai import ai_service as service

router = APIRouter()

@router.get("/", response_model=List[EmbeddingResponse])
def read_embeddings(skip: SkipParam = 0, limit: LimitParam = 100, db: Session = Depends(get_db)):  # type: ignore
    return service.get_embeddings(db, skip=skip, limit=limit)

@router.post("/", response_model=EmbeddingResponse)
def create_embedding(item_in: EmbeddingCreate, db: Session = Depends(get_db)):  # type: ignore
    return service.create_embedding(db, obj_in=item_in)

@router.get("/{id}", response_model=EmbeddingResponse)
def read_embedding(id: UUID, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_embedding(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return db_obj

@router.put("/{id}", response_model=EmbeddingResponse)
def update_embedding(id: UUID, item_in: EmbeddingUpdate, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_embedding(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return service.update_embedding(db, db_obj=db_obj, obj_in=item_in)

@router.delete("/{id}", response_model=EmbeddingResponse)
def delete_embedding(id: UUID, db: Session = Depends(get_db)):  # type: ignore
    db_obj = service.get_embedding(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return service.delete_embedding(db, id=id)
