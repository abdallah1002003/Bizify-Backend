import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.ai_pipeline import GeneralChatRequest, GeneralChatResponse
from app.services.ai_pipeline_service import AIPipelineService

logger = logging.getLogger(__name__)

router = APIRouter()

_AI_BASE_URL = settings.AI_PIPELINE_BASE_URL
_REQUEST_TIMEOUT_SECONDS = 120


@router.post(
    "/general-chat",
    response_model=GeneralChatResponse,
    summary="General Chatbot",
    description="Send a message to the general AI chatbot and get a response.",
)
async def general_chat(
    request: GeneralChatRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    result = await AIPipelineService.general_chat(
        user_id=current_user.id,
        message=request.message,
        history=request.history,
    )
    return result


@router.post(
    "/general-chat/stream",
    summary="General Chatbot Stream",
    description="Send a message to the general AI chatbot and receive a streaming SSE response.",
)
async def general_chat_stream(
    request: GeneralChatRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    stream = AIPipelineService.general_chat_stream(
        user_id=current_user.id,
        message=request.message,
        history=request.history,
    )
    return StreamingResponse(stream, media_type="text/event-stream")


async def _forward_get_to_ai(path: str, user_id: str) -> dict:
    """Helper to fetch data from the external AI pipeline."""
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/{path}/{user_id}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY}
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(target_url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.RequestError as exc:
        logger.error("AI pipeline request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


@router.post("/run", summary="Trigger AI Pipeline")
async def trigger_pipeline(current_user: User = Depends(get_current_user)):
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/run"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(target_url, headers=headers, json={"user_id": str(current_user.id)})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.RequestError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


@router.get("/status", summary="Get Pipeline Status")
async def get_status(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("status", str(current_user.id))


@router.get("/profile", summary="Get Profile Results")
async def get_profile(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("profile", str(current_user.id))


@router.get("/customers", summary="Get Customers Analysis")
async def get_customers(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("customers", str(current_user.id))


@router.get("/competition", summary="Get Competition Analysis")
async def get_competition(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("competition", str(current_user.id))


@router.get("/market-potential", summary="Get Market Potential")
async def get_market_potential(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("market-potential", str(current_user.id))


@router.get("/idea-strategy", summary="Get Idea Strategy")
async def get_idea_strategy(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("idea-strategy", str(current_user.id))


@router.get("/business-model", summary="Get Business Model")
async def get_business_model(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("business-model", str(current_user.id))


@router.get("/functions-list", summary="Get Functions List")
async def get_functions_list(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("functions-list", str(current_user.id))


@router.get("/mvp-planning", summary="Get MVP Planning")
async def get_mvp_planning(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("mvp-planning", str(current_user.id))


@router.get("/unit-economics", summary="Get Unit Economics")
async def get_unit_economics(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("unit-economics", str(current_user.id))


@router.get("/go-to-market", summary="Get Go To Market Strategy")
async def get_go_to_market(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("go-to-market", str(current_user.id))


@router.get("/problems", summary="Get Generated Problems")
async def get_problems(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("problems", str(current_user.id))


@router.get("/idea", summary="Get Generated Idea")
async def get_idea(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("idea", str(current_user.id))
