import logging
from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import check_ai_usage, get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.ai_pipeline import (
    GeneralChatRequest,
    GeneralChatResponse,
    AIPipelineStatusResponse,
    AIProfileResponse,
    AICustomersResponse,
    AICompetitionResponse,
    AIMarketPotentialResponse,
    AIIdeaStrategyResponse,
    AIBusinessModelResponse,
    AIFunctionsListResponse,
    AIMVPPlanningResponse,
    AIUnitEconomicsResponse,
    AIGoToMarketResponse,
    AIProblemsResponse,
    AIIdeaResponse,
)
from app.services.ai_pipeline_service import AIPipelineService

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(check_ai_usage)])

# System endpoints that must NOT require a subscription check
_system_router = APIRouter()

_AI_BASE_URL = settings.AI_PIPELINE_BASE_URL
_REQUEST_TIMEOUT_SECONDS = 120


@router.post(
    "/chat",
    summary="Chatbot",
    description="Send a message to the AI chatbot and get a response.",
    tags=["AI - Chat"],
)
async def chat(
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai("chat", payload=payload)


@router.post(
    "/chat/stream",
    summary="Chatbot Stream",
    description="Send a message to the AI chatbot and receive a streaming SSE response.",
    tags=["AI - Chat"],
)
async def chat_stream(
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai("chat/stream", payload=payload)


@router.post(
    "/general-chat",
    response_model=GeneralChatResponse,
    summary="General Chatbot",
    description="Send a message to the general AI chatbot and get a response.",
    tags=["AI - General Chat"],
)
async def general_chat(
    request: GeneralChatRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await AIPipelineService.general_chat(
        user_id=current_user.id,
        message=request.message,
        history=request.history,
    )


@router.post(
    "/general-chat/stream",
    summary="General Chatbot Stream",
    description="Send a message to the general AI chatbot and receive a streaming SSE response.",
    tags=["AI - General Chat"],
)
async def general_chat_stream(
    request: GeneralChatRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    async def _stream():
        async for chunk in AIPipelineService.general_chat_stream(
            user_id=current_user.id,
            message=request.message,
            history=request.history,
        ):
            yield chunk

    return StreamingResponse(_stream(), media_type="text/event-stream")


async def _forward_get_to_ai(path: str, user_id: str, params: dict | None = None) -> dict:
    """Helper to fetch data from the external AI pipeline."""
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/{path}/{user_id}" if user_id else f"{_AI_BASE_URL}/pipeline/{path}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY}
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(target_url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.RequestError as exc:
        logger.error("AI pipeline request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


async def _forward_post_to_ai(path: str, user_id: str | None = None, payload: dict[str, Any] | None = None) -> dict:
    """Helper to post data to the external AI pipeline."""
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/{path}/{user_id}" if user_id else f"{_AI_BASE_URL}/pipeline/{path}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(target_url, headers=headers, json=payload or {})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.RequestError as exc:
        logger.error("AI pipeline request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")

async def _forward_stream_to_ai(path: str, payload: dict[str, Any] | None = None):
    """Helper to stream data from the external AI pipeline."""
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/{path}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY, "Content-Type": "application/json"}

    async def stream_generator():
        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", target_url, headers=headers, json=payload or {}) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"AI stream error: {exc.response.text}")
        except httpx.RequestError as exc:
            logger.error("AI stream unreachable: %s", exc)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI stream service unreachable.")

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.post("/run", summary="Trigger AI Pipeline", tags=["AI - System"])
async def trigger_pipeline(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/run"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY, "Content-Type": "application/json"}
    body: dict[str, Any] = {"user_id": str(current_user.id)}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(target_url, headers=headers, json=body)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.RequestError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


@router.get("/status", summary="Get Pipeline Status", response_model=AIPipelineStatusResponse, tags=["AI - System"])
async def get_status(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("status", str(current_user.id))


@router.get("/profile", summary="Get Profile Results", response_model=AIProfileResponse, tags=["AI - Profile"])
async def get_profile(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("profile", str(current_user.id))


@router.get("/customers", summary="Get Customers Analysis", response_model=AICustomersResponse, tags=["AI - Customers"])
async def get_customers(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("customers", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)


@router.get("/competition", summary="Get Competition Analysis", response_model=AICompetitionResponse, tags=["AI - Competition"])
async def get_competition(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("competition", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)


@router.get("/market-potential", summary="Get Market Potential", response_model=AIMarketPotentialResponse, tags=["AI - Market Potential"])
async def get_market_potential(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("market-potential", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)


@router.get("/idea-strategy", summary="Get Idea Strategy", response_model=AIIdeaStrategyResponse, tags=["AI - Idea Strategy"])
async def get_idea_strategy(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("idea-strategy", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)


@router.get("/business-model", summary="Get Business Model", response_model=AIBusinessModelResponse, tags=["AI - Business Model"])
async def get_business_model(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("business-model", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)


@router.get("/functions-list", summary="Get Functions List", response_model=AIFunctionsListResponse, tags=["AI - Functions List"])
async def get_functions_list(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("functions-list", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)


@router.get("/mvp-planning", summary="Get MVP Planning", response_model=AIMVPPlanningResponse, tags=["AI - MVP Planning"])
async def get_mvp_planning(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("mvp-planning", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)


@router.get("/unit-economics", summary="Get Unit Economics", response_model=AIUnitEconomicsResponse, tags=["AI - Unit Economics"])
async def get_unit_economics(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("unit-economics", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)


@router.get("/go-to-market", summary="Get Go To Market Strategy", response_model=AIGoToMarketResponse, tags=["AI - Go To Market"])
async def get_go_to_market(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("go-to-market", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)


@router.get("/problems", summary="Get Generated Problems", response_model=AIProblemsResponse, tags=["AI - Problems"])
async def get_problems(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("problems", str(current_user.id))


@router.get("/idea", summary="Get Generated Idea", response_model=AIIdeaResponse, tags=["AI - Idea"])
async def get_idea(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("idea", str(current_user.id), params={"idea_id": idea_id} if idea_id else None)



# ==========================================
# Domain: CUSTOMERS
# ==========================================
@router.post("/customers", summary="Generate Customers", response_model=dict, tags=["AI - Customers"])
async def generate_customers(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("customers", str(current_user.id), payload=body or None)

@router.post("/customers/regenerate", summary="Regenerate Customers", response_model=dict, tags=["AI - Customers"])
async def regenerate_customers(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"customers/{current_user.id}/regenerate", None)

@router.post("/customers/regenerate-custom", summary="Regenerate Customers Custom", response_model=dict, tags=["AI - Customers"])
async def regenerate_custom_customers(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"customers/{current_user.id}/regenerate-custom", payload=payload)

@router.post("/customers/chat", summary="Chat Customers", response_model=dict, tags=["AI - Customers"])
async def chat_customers(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"customers/{current_user.id}/chat", payload=payload)

@router.post("/customers/chat/stream", summary="Chat Customers Stream", tags=["AI - Customers"])
async def chat_stream_customers(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai(f"customers/{current_user.id}/chat/stream", payload=payload)

# ==========================================
# Domain: COMPETITION
# ==========================================
@router.post("/competition", summary="Generate Competition", response_model=dict, tags=["AI - Competition"])
async def generate_competition(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("competition", str(current_user.id), payload=body or None)

@router.post("/competition/regenerate", summary="Regenerate Competition", response_model=dict, tags=["AI - Competition"])
async def regenerate_competition(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"competition/{current_user.id}/regenerate", None)

@router.post("/competition/regenerate-custom", summary="Regenerate Competition Custom", response_model=dict, tags=["AI - Competition"])
async def regenerate_custom_competition(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"competition/{current_user.id}/regenerate-custom", payload=payload)

@router.post("/competition/chat", summary="Chat Competition", response_model=dict, tags=["AI - Competition"])
async def chat_competition(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"competition/{current_user.id}/chat", payload=payload)

@router.post("/competition/chat/stream", summary="Chat Competition Stream", tags=["AI - Competition"])
async def chat_stream_competition(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai(f"competition/{current_user.id}/chat/stream", payload=payload)

# ==========================================
# Domain: MARKET-POTENTIAL
# ==========================================
@router.post("/market-potential", summary="Generate MarketPotential", response_model=dict, tags=["AI - Market Potential"])
async def generate_market_potential(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("market-potential", str(current_user.id), payload=body or None)

@router.post("/market-potential/regenerate", summary="Regenerate MarketPotential", response_model=dict, tags=["AI - Market Potential"])
async def regenerate_market_potential(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"market-potential/{current_user.id}/regenerate", None)

@router.post("/market-potential/regenerate-custom", summary="Regenerate MarketPotential Custom", response_model=dict, tags=["AI - Market Potential"])
async def regenerate_custom_market_potential(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"market-potential/{current_user.id}/regenerate-custom", payload=payload)

@router.post("/market-potential/chat", summary="Chat MarketPotential", response_model=dict, tags=["AI - Market Potential"])
async def chat_market_potential(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"market-potential/{current_user.id}/chat", payload=payload)

@router.post("/market-potential/chat/stream", summary="Chat MarketPotential Stream", tags=["AI - Market Potential"])
async def chat_stream_market_potential(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai(f"market-potential/{current_user.id}/chat/stream", payload=payload)

# ==========================================
# Domain: IDEA-STRATEGY
# ==========================================
@router.post("/idea-strategy", summary="Generate IdeaStrategy", response_model=dict, tags=["AI - Idea Strategy"])
async def generate_idea_strategy(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("idea-strategy", str(current_user.id), payload=body or None)

@router.post("/idea-strategy/regenerate", summary="Regenerate IdeaStrategy", response_model=dict, tags=["AI - Idea Strategy"])
async def regenerate_idea_strategy(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"idea-strategy/{current_user.id}/regenerate", None)

@router.post("/idea-strategy/regenerate-custom", summary="Regenerate IdeaStrategy Custom", response_model=dict, tags=["AI - Idea Strategy"])
async def regenerate_custom_idea_strategy(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"idea-strategy/{current_user.id}/regenerate-custom", payload=payload)

@router.post("/idea-strategy/chat", summary="Chat IdeaStrategy", response_model=dict, tags=["AI - Idea Strategy"])
async def chat_idea_strategy(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"idea-strategy/{current_user.id}/chat", payload=payload)

@router.post("/idea-strategy/chat/stream", summary="Chat IdeaStrategy Stream", tags=["AI - Idea Strategy"])
async def chat_stream_idea_strategy(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai(f"idea-strategy/{current_user.id}/chat/stream", payload=payload)

# ==========================================
# Domain: BUSINESS-MODEL
# ==========================================
@router.post("/business-model", summary="Generate BusinessModel", response_model=dict, tags=["AI - Business Model"])
async def generate_business_model(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("business-model", str(current_user.id), payload=body or None)

@router.post("/business-model/regenerate", summary="Regenerate BusinessModel", response_model=dict, tags=["AI - Business Model"])
async def regenerate_business_model(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"business-model/{current_user.id}/regenerate", None)

@router.post("/business-model/regenerate-custom", summary="Regenerate BusinessModel Custom", response_model=dict, tags=["AI - Business Model"])
async def regenerate_custom_business_model(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"business-model/{current_user.id}/regenerate-custom", payload=payload)

@router.post("/business-model/chat", summary="Chat BusinessModel", response_model=dict, tags=["AI - Business Model"])
async def chat_business_model(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"business-model/{current_user.id}/chat", payload=payload)

@router.post("/business-model/chat/stream", summary="Chat BusinessModel Stream", tags=["AI - Business Model"])
async def chat_stream_business_model(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai(f"business-model/{current_user.id}/chat/stream", payload=payload)

# ==========================================
# Domain: FUNCTIONS-LIST
# ==========================================
@router.post("/functions-list", summary="Generate FunctionsList", response_model=dict, tags=["AI - Functions List"])
async def generate_functions_list(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("functions-list", str(current_user.id), payload=body or None)

@router.post("/functions-list/regenerate", summary="Regenerate FunctionsList", response_model=dict, tags=["AI - Functions List"])
async def regenerate_functions_list(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"functions-list/{current_user.id}/regenerate", None)

@router.post("/functions-list/regenerate-custom", summary="Regenerate FunctionsList Custom", response_model=dict, tags=["AI - Functions List"])
async def regenerate_custom_functions_list(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"functions-list/{current_user.id}/regenerate-custom", payload=payload)

@router.post("/functions-list/chat", summary="Chat FunctionsList", response_model=dict, tags=["AI - Functions List"])
async def chat_functions_list(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"functions-list/{current_user.id}/chat", payload=payload)

@router.post("/functions-list/chat/stream", summary="Chat FunctionsList Stream", tags=["AI - Functions List"])
async def chat_stream_functions_list(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai(f"functions-list/{current_user.id}/chat/stream", payload=payload)

# ==========================================
# Domain: MVP-PLANNING
# ==========================================
@router.post("/mvp-planning", summary="Generate MvpPlanning", response_model=dict, tags=["AI - MVP Planning"])
async def generate_mvp_planning(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("mvp-planning", str(current_user.id), payload=body or None)

@router.post("/mvp-planning/regenerate", summary="Regenerate MvpPlanning", response_model=dict, tags=["AI - MVP Planning"])
async def regenerate_mvp_planning(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"mvp-planning/{current_user.id}/regenerate", None)

@router.post("/mvp-planning/regenerate-custom", summary="Regenerate MvpPlanning Custom", response_model=dict, tags=["AI - MVP Planning"])
async def regenerate_custom_mvp_planning(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"mvp-planning/{current_user.id}/regenerate-custom", payload=payload)

@router.post("/mvp-planning/chat", summary="Chat MvpPlanning", response_model=dict, tags=["AI - MVP Planning"])
async def chat_mvp_planning(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"mvp-planning/{current_user.id}/chat", payload=payload)

@router.post("/mvp-planning/chat/stream", summary="Chat MvpPlanning Stream", tags=["AI - MVP Planning"])
async def chat_stream_mvp_planning(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai(f"mvp-planning/{current_user.id}/chat/stream", payload=payload)

# ==========================================
# Domain: UNIT-ECONOMICS
# ==========================================
@router.post("/unit-economics", summary="Generate UnitEconomics", response_model=dict, tags=["AI - Unit Economics"])
async def generate_unit_economics(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("unit-economics", str(current_user.id), payload=body or None)

@router.post("/unit-economics/regenerate", summary="Regenerate UnitEconomics", response_model=dict, tags=["AI - Unit Economics"])
async def regenerate_unit_economics(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"unit-economics/{current_user.id}/regenerate", None)

@router.post("/unit-economics/regenerate-custom", summary="Regenerate UnitEconomics Custom", response_model=dict, tags=["AI - Unit Economics"])
async def regenerate_custom_unit_economics(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"unit-economics/{current_user.id}/regenerate-custom", payload=payload)

@router.post("/unit-economics/chat", summary="Chat UnitEconomics", response_model=dict, tags=["AI - Unit Economics"])
async def chat_unit_economics(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"unit-economics/{current_user.id}/chat", payload=payload)

@router.post("/unit-economics/chat/stream", summary="Chat UnitEconomics Stream", tags=["AI - Unit Economics"])
async def chat_stream_unit_economics(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai(f"unit-economics/{current_user.id}/chat/stream", payload=payload)

# ==========================================
# Domain: GO-TO-MARKET
# ==========================================
@router.post("/go-to-market", summary="Generate GoToMarket", response_model=dict, tags=["AI - Go To Market"])
async def generate_go_to_market(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("go-to-market", str(current_user.id), payload=body or None)

@router.post("/go-to-market/regenerate", summary="Regenerate GoToMarket", response_model=dict, tags=["AI - Go To Market"])
async def regenerate_go_to_market(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"go-to-market/{current_user.id}/regenerate", None)

@router.post("/go-to-market/regenerate-custom", summary="Regenerate GoToMarket Custom", response_model=dict, tags=["AI - Go To Market"])
async def regenerate_custom_go_to_market(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"go-to-market/{current_user.id}/regenerate-custom", payload=payload)

@router.post("/go-to-market/chat", summary="Chat GoToMarket", response_model=dict, tags=["AI - Go To Market"])
async def chat_go_to_market(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"go-to-market/{current_user.id}/chat", payload=payload)

@router.post("/go-to-market/chat/stream", summary="Chat GoToMarket Stream", tags=["AI - Go To Market"])
async def chat_stream_go_to_market(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai(f"go-to-market/{current_user.id}/chat/stream", payload=payload)

@_system_router.get("/health", summary="Health", tags=["AI - System"])
async def get_health():
    return await _forward_get_to_ai("health", "")

@_system_router.get("/version-check", summary="Version Check", tags=["AI - System"])
async def get_version_check():
    return await _forward_get_to_ai("version-check", "")

@router.get("/questionnaire", summary="Get Questionnaire", tags=["AI - Profile"])
async def get_questionnaire(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("questionnaire", str(current_user.id))

@router.post("/rerun/profile", summary="Rerun Profile", tags=["AI - Profile"])
async def rerun_profile(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai("rerun/profile", str(current_user.id))

@router.post("/rerun/problems", summary="Rerun Problems", tags=["AI - Problems"])
async def rerun_problems(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai("rerun/problems", str(current_user.id))

@router.post("/idea-intake", summary="Idea Intake", tags=["AI - Idea Intake"])
async def idea_intake(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai("idea-intake", payload=payload)

@router.post("/idea-intake/run-problems", summary="Idea Intake Run Problems", tags=["AI - Idea Intake"])
async def idea_intake_run_problems(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"idea-intake/run-problems/{current_user.id}", payload=payload)

@router.post("/idea-intake/start-chat", summary="Idea Intake Start Chat", tags=["AI - Idea Intake"])
async def idea_intake_start_chat(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai("idea-intake/start-chat", payload=payload)

@router.get("/idea-intake", summary="Get Idea Intake", tags=["AI - Idea Intake"])
async def get_idea_intake(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("idea-intake", str(current_user.id))

@router.post("/explain", summary="Explain", tags=["AI - General Chat"])
async def explain(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai("explain", payload=payload)


@router.delete("/ideas/{idea_id}/analysis", status_code=204, summary="Clear Idea Analysis", tags=["AI - Pipeline"])
async def clear_idea_analysis(
    idea_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = str(current_user.id)
    iid = str(idea_id)
    for table in [
        "idea_results",
        "idea_intake_results",
        "customers_results",
        "competition_results",
        "market_potential_results",
        "idea_strategy_results",
        "business_model_results",
        "functions_list_results",
        "mvp_planning_results",
        "unit_economics_results",
        "go_to_market_results",
    ]:
        db.execute(text(f"DELETE FROM {table} WHERE user_id = :uid AND idea_id = :iid"), {"uid": uid, "iid": iid})
    db.commit()
