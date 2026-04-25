import logging
import json

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.ai_pipeline import AIPipelineResponse
from app.services.ai_pipeline_service import AIPipelineService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AIPipelineResponse,
    summary="Run AI Pipeline",
    description=(
        "Reads the current user's questionnaire answers from the database and "
        "forwards them to the external AI pipeline for analysis. "
        "No request body needed — the profile is fetched automatically."
    ),
)
async def run_ai_pipeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIPipelineResponse:
    """Build payload from user's stored profile and proxy it to the AI pipeline."""
    try:
        result = await AIPipelineService.run(db=db, user_id=current_user.id)
        return AIPipelineResponse(success=True, result=result)

    except httpx.HTTPStatusError as exc:
        logger.error(
            "AI pipeline returned HTTP %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI pipeline error: {exc.response.text}",
        ) from exc

    except httpx.RequestError as exc:
        logger.error("AI pipeline request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the AI pipeline. Please try again later.",
        ) from exc


@router.get(
    "/analyze/status",
    summary="Check AI Pipeline Status",
    description="Check the current progress of the AI pipeline for the logged-in user.",
)
async def get_ai_pipeline_status(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Proxy the status check to the external AI pipeline."""
    try:
        return await AIPipelineService.get_status(user_id=current_user.id)
            
    except httpx.HTTPStatusError as exc:
        logger.error("AI pipeline status returned HTTP %s", exc.response.status_code)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI pipeline error: {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("AI pipeline status request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the AI pipeline. Please try again later.",
        ) from exc



@router.get(
    "/analyze/results",
    summary="Get AI Pipeline Results",
    description="Fetch the final generated results from the AI pipeline, save them to the database, and return them.",
)
async def get_ai_pipeline_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Proxy the results fetching to the external AI pipeline and save to DB."""
    try:
        results = await AIPipelineService.get_results(user_id=current_user.id)
        
        if current_user.profile:
            current_user.profile.personalization_profile = json.dumps(results)
            db.commit()
            
        return results
            
    except httpx.HTTPStatusError as exc:
        logger.error("AI pipeline results returned HTTP %s", exc.response.status_code)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI pipeline error: {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("AI pipeline results request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the AI pipeline. Please try again later.",
        ) from exc
