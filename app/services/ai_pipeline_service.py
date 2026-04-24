import logging
import uuid
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_AI_PIPELINE_URL = "https://bizifyai-production.up.railway.app/pipeline/run"
_AI_PIPELINE_API_KEY = "7f986c28-88d1-424d-8622-776ffaff3452"
_REQUEST_TIMEOUT_SECONDS = 30


class AIPipelineService:
    """Service responsible for communicating with the external AI pipeline."""

    @staticmethod
    def _build_payload(db: Session, user_id: uuid.UUID) -> dict:
        """
        Build the request body for the AI pipeline from the user's stored profile data.

        Schema matches the questionnaire output:
        {
          "user_profile": { curiosity_domain, experience_level, business_interests,
                            target_region, founder_setup, risk_tolerance },
          "career_profile": { free_day_preferences, preferred_work_types,
                              problem_solving_styles, preferred_work_environments,
                              desired_impact }
        }
        """
        from app.models.user_profile import UserProfile

        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        
        user_profile_data = profile.background_json if profile and profile.background_json else {}
        career_profile_data = profile.personality_json if profile and profile.personality_json else {}

        def single(data: dict, key: str) -> str:
            val = data.get(key)
            if isinstance(val, list):
                return val[0] if val else ""
            return val or ""

        def multi(data: dict, key: str) -> list:
            val = data.get(key)
            if isinstance(val, list):
                return val
            if val:
                return [val]
            return []

        return {
            "user_id": str(user_id),
            "user_profile": {
                "curiosity_domain":   single(user_profile_data, "curiosity_domain"),
                "experience_level":   single(user_profile_data, "experience_level"),
                "business_interests": multi(user_profile_data, "business_interests"),
                "target_region":      single(user_profile_data, "target_region"),
                "founder_setup":      single(user_profile_data, "founder_setup"),
                "risk_tolerance":     single(user_profile_data, "risk_tolerance"),
            },
            "career_profile": {
                "free_day_preferences":       multi(career_profile_data, "free_day_preferences"),
                "preferred_work_types":       multi(career_profile_data, "preferred_work_types"),
                "problem_solving_styles":     multi(career_profile_data, "problem_solving_styles"),
                "preferred_work_environments": multi(career_profile_data, "preferred_work_environments"),
                "desired_impact":             multi(career_profile_data, "desired_impact"),
            },
        }

    @staticmethod
    async def run(
        db: Session,
        user_id: uuid.UUID,
        payload: Optional[Any] = None,
    ) -> dict:
        """
        Forward the user's profile data to the AI pipeline and return the parsed JSON response.

        Args:
            db:       SQLAlchemy session (used to fetch user data).
            user_id:  The ID of the user whose profile is sent.
            payload:  Optional manual override — if provided, skips DB lookup.

        Returns:
            The JSON response from the pipeline as a plain dict.

        Raises:
            httpx.HTTPStatusError: When the pipeline returns a 4xx / 5xx response.
            httpx.RequestError:    On network / timeout failures.
        """
        headers = {
            "x-api-key": _AI_PIPELINE_API_KEY,
            "Content-Type": "application/json",
        }

        body: dict = payload if payload is not None else AIPipelineService._build_payload(db, user_id)

        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            logger.info("Calling AI pipeline for user %s: %s", user_id, _AI_PIPELINE_URL)
            response = await client.post(
                _AI_PIPELINE_URL,
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            logger.info("AI pipeline responded with status %s", response.status_code)
            return response.json()
