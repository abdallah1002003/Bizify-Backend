from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.ideation.idea import IdeaCreate, IdeaUpdate, IdeaResponse
from app.services.ideation.idea_service import IdeaService, get_idea_service
from app.core.dependencies import get_current_active_user
import app.models as models
from app.core.cache import get_cache_manager

router = APIRouter()

@router.get("/", response_model=List[IdeaResponse])
def read_ideas(  # type: ignore
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """List ideas visible to current user with pagination (cached)."""
    cache = get_cache_manager()
    gen = cache.get_generation_key(f"ideas:{current_user.id}")
    cache_key = f"api:ideas:{current_user.id}:v={gen}:skip={skip}:limit={limit}"
    
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = service.get_ideas(skip=skip, limit=limit, user_id=current_user.id)
    
    # Store directly; FastAPI will validate it through the response_model
    cache.set(cache_key, result, ttl_seconds=300)
    return result

@router.post("/", response_model=IdeaResponse)
def create_idea(  # type: ignore
    item_in: IdeaCreate, 
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elite API: Secure idea creation with auto-versioning."""
    item_in.owner_id = current_user.id or item_in.owner_id
    result = service.create_idea(obj_in=item_in)
    
    get_cache_manager().increment_generation_key(f"ideas:{current_user.id}")
    return result

@router.get("/{id}", response_model=IdeaResponse)
def read_idea(  # type: ignore
    id: UUID, 
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elite API: RBAC-verified retrieval."""
    cache = get_cache_manager()
    cache_key = f"api:idea:{id}:user:{current_user.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    db_obj = service.get_idea(id=id, user_id=current_user.id)
    if not db_obj: 
        raise HTTPException(status_code=404, detail="Idea not found")
        
    cache.set(cache_key, db_obj, ttl_seconds=300)
    return db_obj

@router.put("/{id}", response_model=IdeaResponse)
def update_idea(  # type: ignore
    id: UUID, 
    item_in: IdeaUpdate, 
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elite API: Protected mutation with lineage tracking."""
    db_obj = service.get_idea(id=id)
    if not db_obj:
         raise HTTPException(status_code=404, detail="Idea not found")
         
    result = service.update_idea(db_obj=db_obj, obj_in=item_in, performer_id=current_user.id)
    
    cache = get_cache_manager()
    cache.increment_generation_key(f"ideas:{current_user.id}")
    cache.delete(f"api:idea:{id}:user:{current_user.id}")
    return result

@router.delete("/{id}", response_model=IdeaResponse)
def delete_idea(  # type: ignore
    id: UUID, 
    service: IdeaService = Depends(get_idea_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elite API: Secure deletion with ownership verification."""
    if not service.check_idea_access(id, current_user.id, "delete"):
        raise HTTPException(status_code=403, detail="Ownership required for deletion")
        
    result = service.delete_idea(id=id)
    
    cache = get_cache_manager()
    cache.increment_generation_key(f"ideas:{current_user.id}")
    cache.delete(f"api:idea:{id}:user:{current_user.id}")
    return result
