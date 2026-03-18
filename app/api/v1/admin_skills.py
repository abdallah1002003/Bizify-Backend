import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api import dependencies
from app.models.industry import Industry
from app.models.skill_benchmark import SkillBenchmark
from app.models.user import User, UserRole
from app.schemas.skill_gap import (
    IndustryCreate,
    IndustryResponse,
    SkillBenchmarkCreate,
    SkillBenchmarkResponse,
)


router = APIRouter()


@router.post("/benchmarks", response_model = SkillBenchmarkResponse, status_code = status.HTTP_201_CREATED)
def create_benchmark(
    obj_in: SkillBenchmarkCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.RoleChecker([UserRole.ADMIN]))
) -> Any:
    """
    Admin only: Creates a new skill benchmark for a specific industry tier.
    """
    db_obj = SkillBenchmark(**obj_in.model_dump())
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj


@router.get("/benchmarks", response_model = List[SkillBenchmarkResponse])
def list_benchmarks(
    industry_id: Optional[uuid.UUID] = None,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user)
) -> Any:
    """
    Retrieves a list of all skill benchmarks, optionally filtering by industry.
    """
    query = db.query(SkillBenchmark)
    
    if industry_id:
        query = query.filter(SkillBenchmark.industry_id == industry_id)
        
    return query.all()


@router.post("/industries", response_model = IndustryResponse, status_code = status.HTTP_201_CREATED)
def create_industry(
    obj_in: IndustryCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.RoleChecker([UserRole.ADMIN]))
) -> Any:
    """
    Admin only: Initializes a new industry or specialized niche in the hierarchy.
    """
    db_obj = Industry(**obj_in.model_dump())
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj


@router.get("/industries", response_model = List[IndustryResponse])
def list_industries(
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user)
) -> Any:
    """
    Retrieves the complete hierarchical registry of industries.
    """
    return db.query(Industry).all()


@router.delete("/benchmarks/{benchmark_id}", status_code = status.HTTP_204_NO_CONTENT, response_class = Response)
def delete_benchmark(
    benchmark_id: uuid.UUID,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.RoleChecker([UserRole.ADMIN]))
) -> None:
    """
    Admin only: Removes a specific skill benchmark from the system.
    """
    db_obj = db.query(SkillBenchmark).filter(SkillBenchmark.id == benchmark_id).first()
    
    if not db_obj:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Benchmark not found"
        )
    
    db.delete(db_obj)
    db.commit()
    
    return None


@router.delete("/industries/{industry_id}", status_code = status.HTTP_204_NO_CONTENT, response_class = Response)
def delete_industry(
    industry_id: uuid.UUID,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.RoleChecker([UserRole.ADMIN]))
) -> None:
    """
    Admin only: Removes an industry, provided it has no dependencies (benchmarks or sub-industries).
    """
    db_obj = db.query(Industry).filter(Industry.id == industry_id).first()
    
    if not db_obj:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Industry not found"
        )
    
    # Validation: prevent orphan benchmarks or broken sub-hierarchies
    has_benchmarks = db.query(SkillBenchmark).filter(SkillBenchmark.industry_id == industry_id).first()
    has_children = db.query(Industry).filter(Industry.parent_id == industry_id).first()
    
    if has_benchmarks or has_children:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "Cannot delete industry that has sub-industries or benchmarks linked to it."
        )

    db.delete(db_obj)
    db.commit()
    
    return None


@router.put("/benchmarks/{benchmark_id}", response_model = SkillBenchmarkResponse)
def update_benchmark(
    benchmark_id: uuid.UUID,
    obj_in: SkillBenchmarkCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.RoleChecker([UserRole.ADMIN]))
) -> Any:
    """
    Admin only: Modifies an existing skill benchmark's criteria.
    """
    db_obj = db.query(SkillBenchmark).filter(SkillBenchmark.id == benchmark_id).first()
    
    if not db_obj:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Benchmark not found"
        )
    
    update_data = obj_in.model_dump()
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj


@router.put("/industries/{industry_id}", response_model = IndustryResponse)
def update_industry(
    industry_id: uuid.UUID,
    obj_in: IndustryCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.RoleChecker([UserRole.ADMIN]))
) -> Any:
    """
    Admin only: Updates the metadata of an existing industry or niche.
    """
    db_obj = db.query(Industry).filter(Industry.id == industry_id).first()
    
    if not db_obj:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Industry not found"
        )
    
    update_data = obj_in.model_dump()
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj
