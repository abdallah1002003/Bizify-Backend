import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import dependencies
from app.models.user import User
from app.schemas.skill_gap import SkillGapReportResponse, UserSkillsInput, UserSkill
from app.services.skill_gap_service import SkillGapService


router = APIRouter()


@router.post("/analyze", response_model = SkillGapReportResponse, status_code = status.HTTP_200_OK)
def analyze_user_skills(
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user)
) -> Any:
    """
    UC_11: BF_01 to BF_08 - Triggers the automated skill gap analysis for the authenticated user.
    """
    return SkillGapService.analyze_user_skills(db, current_user.id)


@router.get("/report", response_model = SkillGapReportResponse)
def get_latest_report(
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user)
) -> Any:
    """
    UC_11: BF_09 - Fetches the most recent skill gap analysis report for the user.
    """
    report = SkillGapService.get_user_report(db, current_user.id)
    if report is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "No skill gap report found. Please run /skills/analyze first."
        )
    return report


@router.post("/update-profile", response_model = List[UserSkill], status_code = status.HTTP_200_OK)
def update_profile_skills(
    skills_input: UserSkillsInput,
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user)
) -> Any:
    """
    Updates the user's declared skills and triggers dependency invalidation for re-analysis.
    """
    return SkillGapService.update_user_skills(db, current_user.id, skills_input.skills)


@router.post("/skip", status_code = status.HTTP_200_OK)
def skip_questionnaire(
    db: Session = Depends(dependencies.get_db),
    current_user: User = Depends(dependencies.get_current_user)
) -> Dict[str, Any]:
    """
    UC_11: AF_A6 - Allows the user to bypass the skills questionnaire for now.
    """
    success = SkillGapService.skip_skills_questionnaire(db, current_user.id)
    
    return {
        "success": success, 
        "message": "Questionnaire skipped successfully."
    }
