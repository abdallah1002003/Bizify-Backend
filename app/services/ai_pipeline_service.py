import asyncio
import logging
import uuid
from typing import Any, AsyncGenerator, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

_AI_PIPELINE_URL = "https://bizifyai-production.up.railway.app/pipeline/run"
_REQUEST_TIMEOUT_SECONDS = 120


class AIPipelineService:
    """Service responsible for communicating with the external AI pipeline."""

    @staticmethod
    def _build_payload(db: Session, user_id: uuid.UUID) -> dict:
        """
        Build the request body for the AI pipeline.
        The pipeline now reads questionnaire/skills directly from the database,
        so only user_id is needed.
        """
        return {"user_id": str(user_id)}

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
            "x-api-key": settings.AI_PIPELINE_API_KEY,
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

    @staticmethod
    async def get_status(user_id: uuid.UUID) -> dict:
        """Fetch the current progress of the AI pipeline for the given user."""
        url = f"{_AI_PIPELINE_URL.rsplit('/', 1)[0]}/status/{user_id}"
        headers = {
            "x-api-key": settings.AI_PIPELINE_API_KEY,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_results(user_id: uuid.UUID) -> dict:
        """Fetch the final generated results from the AI pipeline."""
        base_url = _AI_PIPELINE_URL.rsplit('/pipeline', 1)[0]
        headers = {
            "x-api-key": settings.AI_PIPELINE_API_KEY,
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            profile_res, problems_res, idea_res = await asyncio.gather(
                client.get(f"{base_url}/pipeline/profile/{user_id}", headers=headers),
                client.get(f"{base_url}/pipeline/problems/{user_id}", headers=headers),
                client.get(f"{base_url}/pipeline/idea/{user_id}", headers=headers),
            )
            
            profile_res.raise_for_status()
            problems_res.raise_for_status()
            idea_res.raise_for_status()
            
            return {
                "profile_analysis": profile_res.json().get("profile_analysis"),
                "problems": problems_res.json().get("problems", []),
                "idea": idea_res.json().get("current_idea"),
                "chat_history": idea_res.json().get("chat_history", [])
            }

    @staticmethod
    async def general_chat(
        user_id: uuid.UUID,
        message: str,
        history: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Send a message to the General Chatbot and return the response."""
        url = f"{_AI_PIPELINE_URL.rsplit('/run', 1)[0]}/general-chat"
        headers = {
            "x-api-key": settings.AI_PIPELINE_API_KEY,
            "Content-Type": "application/json",
        }
        body = {
            "user_id": str(user_id),
            "message": message,
            "history": history or [],
        }
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            try:
                response = await client.post(url, headers=headers, json=body)
                if response.is_error:
                    logger.error("AI General Chat failed with status %s: %s", response.status_code, response.text)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                raise HTTPException(status_code=exc.response.status_code, detail=f"AI Chat error: {exc.response.text}")
            except Exception as exc:
                logger.exception("AI General Chat failed")
                raise HTTPException(status_code=500, detail="Internal error communicating with AI Chat")

    @staticmethod
    async def general_chat_stream(
        user_id: uuid.UUID,
        message: str,
        history: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Stream a response from the General Chatbot."""
        url = f"{_AI_PIPELINE_URL.rsplit('/run', 1)[0]}/general-chat/stream"
        headers = {
            "x-api-key": settings.AI_PIPELINE_API_KEY,
            "Content-Type": "application/json",
        }
        body = {
            "user_id": str(user_id),
            "message": message,
            "history": history or [],
        }
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            async with client.stream("POST", url, headers=headers, json=body) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk
