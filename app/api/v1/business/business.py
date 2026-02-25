from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from app.schemas.business.business import BusinessCreate, BusinessUpdate, BusinessResponse
from app.services.business.business_service import BusinessService, get_business_service
from app.core import dependencies
import app.models as models
from app.core.cache import get_cache_manager

router = APIRouter()

@router.get("/", response_model=List[BusinessResponse])
def read_businesses(  # type: ignore
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """List businesses owned by current user with pagination."""
    cache = get_cache_manager()
    gen = cache.get_generation_key(f"businesses:{current_user.id}")
    cache_key = f"api:businesses:{current_user.id}:v={gen}:skip={skip}:limit={limit}"
    
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = service.get_businesses(skip=skip, limit=limit, owner_id=current_user.id)
    cache.set(cache_key, result, ttl_seconds=300)
    return result

@router.post("/", response_model=BusinessResponse)
def create_business(  # type: ignore
    item_in: BusinessCreate, 
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Logic-injected creation (auto-roadmap/collaborator)."""
    item_in.owner_id = current_user.id or item_in.owner_id
    result = service.create_business(obj_in=item_in)
    
    get_cache_manager().increment_generation_key(f"businesses:{current_user.id}")
    return result

@router.get("/{id}", response_model=BusinessResponse)
def read_business(  # type: ignore
    id: UUID, 
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Secure retrieval."""
    cache = get_cache_manager()
    cache_key = f"api:business:{id}:user:{current_user.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
        
    db_obj = service.get_business(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Business not found")
    # Ownership Check
    if db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    cache.set(cache_key, db_obj, ttl_seconds=300)
    return db_obj

@router.put("/{id}", response_model=BusinessResponse)
def update_business(  # type: ignore
    id: UUID, item_in: BusinessUpdate, 
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Protected mutation."""
    db_obj = service.get_business(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Business not found")
    if db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ownership required")
        
    result = service.update_business(db_obj=db_obj, obj_in=item_in)
    
    cache = get_cache_manager()
    cache.increment_generation_key(f"businesses:{current_user.id}")
    cache.delete(f"api:business:{id}:user:{current_user.id}")
    return result

@router.delete("/{id}", response_model=BusinessResponse)
def delete_business(  # type: ignore
    id: UUID, 
    service: BusinessService = Depends(get_business_service),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """Elite API: Destructive operation guard."""
    db_obj = service.get_business(id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Business not found")
    if db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Destructive admin rights required")
        
    result = service.delete_business(id=id)
    
    cache = get_cache_manager()
    cache.increment_generation_key(f"businesses:{current_user.id}")
    cache.delete(f"api:business:{id}:user:{current_user.id}")
    return result
