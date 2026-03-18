import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas import guidance as schemas
from app.services.guidance_service import GuidanceService


router = APIRouter()


@router.get("/stages", response_model = List[schemas.GuidanceStage])
def read_stages(db: Session = Depends(get_db)) -> List[schemas.GuidanceStage]:
    """
    Get all stages of business guidance, ordered by sequence.
    """
    return GuidanceService.get_all_stages(db)


@router.get("/stages/{stage_id}/concepts", response_model = List[schemas.GuidanceConcept])
def read_concepts(
    stage_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> List[schemas.GuidanceConcept]:
    """
    Get all concepts for a specific stage.
    """
    return GuidanceService.get_concepts_by_stage(db, stage_id)


@router.get("/concepts/{concept_id}", response_model = schemas.GuidanceConcept)
def read_concept(
    concept_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> schemas.GuidanceConcept:
    """
    Get the details of a specific business concept.
    """
    return GuidanceService.get_concept_detail(db, concept_id)


@router.post("/progress/{concept_id}", response_model = schemas.UserConceptState)
def update_progress(
    concept_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> schemas.UserConceptState:
    """
    Updates the user's progress by marking the last concept they viewed.
    """
    return GuidanceService.update_user_progress(db, current_user.id, concept_id)


@router.get("/progress", response_model = schemas.UserConceptState)
def read_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> schemas.UserConceptState:
    """
    Retrieves the last point the user reached in the guidance system.
    """
    progress = GuidanceService.get_user_progress(db, current_user.id)
    
    if not progress:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "No progress found"
        )
        
    return progress
