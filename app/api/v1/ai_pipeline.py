import logging
from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import check_ai_usage, get_current_user, get_db
from app.constants.credit_costs import SECTION_CREDIT_COSTS
from app.core.database import SessionLocal
from app.repositories.billing_repo import subscription_repo
from app.repositories.usage_repo import usage_repo as _usage_repo
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


def _http_exception_from_upstream(response: httpx.Response) -> HTTPException:
    """
    Translate an upstream AI-service error without leaking internal details.

    4xx responses carry user-meaningful messages and are forwarded as-is; 5xx
    responses are logged server-side and surfaced to the client as a generic
    502 so internal stack traces / exception text never reach the browser.
    """
    if response.status_code >= 500:
        logger.error("AI pipeline upstream %s: %s", response.status_code, response.text[:500])
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service error. Please try again later.",
        )
    detail = "AI service error."
    try:
        data = response.json()
        if isinstance(data, dict) and "detail" in data:
            detail = str(data["detail"])[:500]
    except Exception:
        pass
    return HTTPException(status_code=response.status_code, detail=detail)


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
    return await _forward_post_to_ai("chat", payload=payload, extra_headers=_ai_headers(current_user))


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
    return await _forward_stream_to_ai("chat/stream", payload=payload, extra_headers=_ai_headers(current_user))


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
    result = await AIPipelineService.general_chat(
        user_id=current_user.id,
        message=request.message,
        history=request.history,
        settings_language=request.settings_language,
    )
    # Bug fix: when generalBot triggers a full section run internally, the cost
    # of that section run was not charged (only the 0-credit chat gate ran).
    # Deduct the section credits here, after the fact.
    if result.get("intent") == "run_section" and result.get("action") == "triggered":
        section = (result.get("section") or "").replace("-", "_")
        cost = SECTION_CREDIT_COSTS.get(section, 0)
        if cost > 0:
            try:
                db = SessionLocal()
                try:
                    _usage_repo.deduct_credits(db, current_user.id, cost)
                finally:
                    db.close()
            except Exception:
                logger.warning("Failed to charge section credits for run_section intent (section=%s)", section)
    return result


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
            settings_language=request.settings_language,
        ):
            yield chunk

    return StreamingResponse(_stream(), media_type="text/event-stream")


def _get_plan_name(user: User) -> str:
    """Return the user's active plan name, or 'Free' if they have none.
    Opens its own short-lived session so callers don't need db injected."""
    try:
        db = SessionLocal()
        try:
            sub = subscription_repo.get_active_by_user(db, user.id)
            if sub and sub.plan:
                return sub.plan.name
        finally:
            db.close()
    except Exception:
        pass
    return "Free"


def _ai_headers(user: User) -> dict:
    """Build the standard AI service request headers including plan name."""
    return {"x-plan-name": _get_plan_name(user)}


def _resolve_ai_user_id(
    current_user: User,
    idea_id: Optional[str],
    *,
    require_edit: bool = False,
) -> str:
    """
    Resolve which user_id the AI service should be addressed with.

    AI section results (customers_results, competition_results, …) are keyed by
    (user_id, idea_id) where user_id is the idea OWNER. When a team member opens
    a shared idea, forwarding their own id finds nothing — every section 404s and
    the shared view looks empty. For shared ideas we therefore forward the
    OWNER's id, after verifying the requester actually has access:

      • require_edit=False → any group member with access to the idea (viewers)
      • require_edit=True  → owner or group OWNER/EDITOR roles only

    Falls back to the requester's own id when no idea_id is given (legacy
    single-idea flows) or the idea is their own.
    """
    if not idea_id:
        return str(current_user.id)
    try:
        idea_uuid = UUID(str(idea_id))
    except (ValueError, AttributeError, TypeError):
        return str(current_user.id)

    from app.repositories.idea_repo import idea_repo
    from app.services.idea_service import IdeaService

    db = SessionLocal()
    try:
        idea = idea_repo.get(db, id=idea_uuid)
        if not idea or idea.owner_id == current_user.id:
            return str(current_user.id)

        if require_edit:
            if not IdeaService._can_edit_idea(db, idea_uuid, current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to modify this idea.",
                )
        else:
            accessible = {i.id for i in IdeaService._get_accessible_ideas(db, current_user.id)}
            if idea_uuid not in accessible:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this idea.",
                )
        return str(idea.owner_id)
    finally:
        db.close()


async def _forward_get_to_ai(
    path: str,
    user_id: str,
    params: Optional[dict] = None,
    extra_headers: Optional[dict] = None,
) -> dict:
    """Helper to fetch data from the external AI pipeline."""
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/{path}/{user_id}" if user_id else f"{_AI_BASE_URL}/pipeline/{path}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY, **(extra_headers or {})}
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(target_url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise _http_exception_from_upstream(exc.response)
    except httpx.RequestError as exc:
        logger.error("AI pipeline request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


async def _forward_post_to_ai(
    path: str,
    user_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
    extra_headers: Optional[dict] = None,
    timeout: int = _REQUEST_TIMEOUT_SECONDS,
) -> dict:
    """Helper to post data to the external AI pipeline."""
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/{path}/{user_id}" if user_id else f"{_AI_BASE_URL}/pipeline/{path}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY, "Content-Type": "application/json", **(extra_headers or {})}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(target_url, headers=headers, json=payload or {})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise _http_exception_from_upstream(exc.response)
    except httpx.RequestError as exc:
        logger.error("AI pipeline request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


async def _forward_stream_to_ai(
    path: str,
    payload: Optional[dict[str, Any]] = None,
    extra_headers: Optional[dict] = None,
):
    """Helper to stream data from the external AI pipeline."""
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/{path}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY, "Content-Type": "application/json", **(extra_headers or {})}

    async def stream_generator():
        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", target_url, headers=headers, json=payload or {}) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except httpx.HTTPStatusError as exc:
            raise _http_exception_from_upstream(exc.response)
        except httpx.RequestError as exc:
            logger.error("AI stream unreachable: %s", exc)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI stream service unreachable.")

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


async def _forward_write_to_ai(
    method: str,
    path: str,
    payload: Optional[dict[str, Any]] = None,
    params: Optional[dict] = None,
    extra_headers: Optional[dict] = None,
) -> dict:
    """
    Forward a PATCH/DELETE/PUT to the AI pipeline. `path` is the full AI path
    after /pipeline/ (e.g. "roadmap/task/<id>/status") — no user_id is appended.
    """
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/{path}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY, "Content-Type": "application/json", **(extra_headers or {})}
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.request(method, target_url, headers=headers, json=payload, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise _http_exception_from_upstream(exc.response)
    except httpx.RequestError as exc:
        logger.error("AI pipeline request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


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
        raise _http_exception_from_upstream(exc.response)
    except httpx.RequestError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


@router.get("/status", summary="Get Pipeline Status", response_model=AIPipelineStatusResponse, tags=["AI - System"])
async def get_status(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("status", str(current_user.id), extra_headers=_ai_headers(current_user))


@router.get("/profile", summary="Get Profile Results", response_model=AIProfileResponse, tags=["AI - Profile"])
async def get_profile(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("profile", str(current_user.id), extra_headers=_ai_headers(current_user))


@router.get("/customers", summary="Get Customers Analysis", response_model=AICustomersResponse, tags=["AI - Customers"])
async def get_customers(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("customers", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/competition", summary="Get Competition Analysis", response_model=AICompetitionResponse, tags=["AI - Competition"])
async def get_competition(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("competition", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/market-potential", summary="Get Market Potential", response_model=AIMarketPotentialResponse, tags=["AI - Market Potential"])
async def get_market_potential(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("market-potential", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/idea-strategy", summary="Get Idea Strategy", response_model=AIIdeaStrategyResponse, tags=["AI - Idea Strategy"])
async def get_idea_strategy(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("idea-strategy", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/business-model", summary="Get Business Model", response_model=AIBusinessModelResponse, tags=["AI - Business Model"])
async def get_business_model(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("business-model", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/functions-list", summary="Get Functions List", response_model=AIFunctionsListResponse, tags=["AI - Functions List"])
async def get_functions_list(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("functions-list", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/mvp-planning", summary="Get MVP Planning", response_model=AIMVPPlanningResponse, tags=["AI - MVP Planning"])
async def get_mvp_planning(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("mvp-planning", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/unit-economics", summary="Get Unit Economics", response_model=AIUnitEconomicsResponse, tags=["AI - Unit Economics"])
async def get_unit_economics(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("unit-economics", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/go-to-market", summary="Get Go To Market Strategy", response_model=AIGoToMarketResponse, tags=["AI - Go To Market"])
async def get_go_to_market(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("go-to-market", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/problems", summary="Get Generated Problems", response_model=AIProblemsResponse, tags=["AI - Problems"])
async def get_problems(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("problems", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/idea", summary="Get Generated Idea", response_model=AIIdeaResponse, tags=["AI - Idea"])
async def get_idea(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("idea", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.post("/ideas/{idea_id}/suggest-name", summary="Suggest catchy startup names", tags=["AI - Idea"])
async def suggest_idea_name(idea_id: UUID, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, str(idea_id), require_edit=True)
    return await _forward_post_to_ai(f"suggest-name/{ai_user}", None, {"idea_id": str(idea_id)}, extra_headers=_ai_headers(current_user))


# ==========================================
# Domain: CUSTOMERS
# ==========================================
@router.post("/customers", summary="Generate Customers", response_model=dict, tags=["AI - Customers"])
async def generate_customers(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("customers", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/customers/regenerate", summary="Regenerate Customers", response_model=dict, tags=["AI - Customers"])
async def regenerate_customers(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"customers/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/customers/regenerate-custom", summary="Regenerate Customers Custom", response_model=dict, tags=["AI - Customers"])
async def regenerate_custom_customers(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"customers/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/customers/chat", summary="Chat Customers", response_model=dict, tags=["AI - Customers"])
async def chat_customers(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"customers/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/customers/chat/stream", summary="Chat Customers Stream", tags=["AI - Customers"])
async def chat_stream_customers(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"customers/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: COMPETITION
# ==========================================
@router.post("/competition", summary="Generate Competition", response_model=dict, tags=["AI - Competition"])
async def generate_competition(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("competition", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/competition/regenerate", summary="Regenerate Competition", response_model=dict, tags=["AI - Competition"])
async def regenerate_competition(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"competition/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/competition/regenerate-custom", summary="Regenerate Competition Custom", response_model=dict, tags=["AI - Competition"])
async def regenerate_custom_competition(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"competition/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/competition/chat", summary="Chat Competition", response_model=dict, tags=["AI - Competition"])
async def chat_competition(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"competition/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/competition/chat/stream", summary="Chat Competition Stream", tags=["AI - Competition"])
async def chat_stream_competition(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"competition/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: MARKET-POTENTIAL
# ==========================================
@router.post("/market-potential", summary="Generate MarketPotential", response_model=dict, tags=["AI - Market Potential"])
async def generate_market_potential(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("market-potential", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/market-potential/regenerate", summary="Regenerate MarketPotential", response_model=dict, tags=["AI - Market Potential"])
async def regenerate_market_potential(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"market-potential/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/market-potential/regenerate-custom", summary="Regenerate MarketPotential Custom", response_model=dict, tags=["AI - Market Potential"])
async def regenerate_custom_market_potential(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"market-potential/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/market-potential/chat", summary="Chat MarketPotential", response_model=dict, tags=["AI - Market Potential"])
async def chat_market_potential(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"market-potential/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/market-potential/chat/stream", summary="Chat MarketPotential Stream", tags=["AI - Market Potential"])
async def chat_stream_market_potential(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"market-potential/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: IDEA-STRATEGY
# ==========================================
@router.post("/idea-strategy", summary="Generate IdeaStrategy", response_model=dict, tags=["AI - Idea Strategy"])
async def generate_idea_strategy(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("idea-strategy", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/idea-strategy/regenerate", summary="Regenerate IdeaStrategy", response_model=dict, tags=["AI - Idea Strategy"])
async def regenerate_idea_strategy(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"idea-strategy/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/idea-strategy/regenerate-custom", summary="Regenerate IdeaStrategy Custom", response_model=dict, tags=["AI - Idea Strategy"])
async def regenerate_custom_idea_strategy(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"idea-strategy/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/idea-strategy/chat", summary="Chat IdeaStrategy", response_model=dict, tags=["AI - Idea Strategy"])
async def chat_idea_strategy(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"idea-strategy/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/idea-strategy/chat/stream", summary="Chat IdeaStrategy Stream", tags=["AI - Idea Strategy"])
async def chat_stream_idea_strategy(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"idea-strategy/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: BUSINESS-MODEL
# ==========================================
@router.post("/business-model", summary="Generate BusinessModel", response_model=dict, tags=["AI - Business Model"])
async def generate_business_model(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("business-model", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/business-model/regenerate", summary="Regenerate BusinessModel", response_model=dict, tags=["AI - Business Model"])
async def regenerate_business_model(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"business-model/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/business-model/regenerate-custom", summary="Regenerate BusinessModel Custom", response_model=dict, tags=["AI - Business Model"])
async def regenerate_custom_business_model(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"business-model/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/business-model/chat", summary="Chat BusinessModel", response_model=dict, tags=["AI - Business Model"])
async def chat_business_model(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"business-model/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/business-model/chat/stream", summary="Chat BusinessModel Stream", tags=["AI - Business Model"])
async def chat_stream_business_model(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"business-model/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: FUNCTIONS-LIST
# ==========================================
@router.post("/functions-list", summary="Generate FunctionsList", response_model=dict, tags=["AI - Functions List"])
async def generate_functions_list(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("functions-list", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/functions-list/regenerate", summary="Regenerate FunctionsList", response_model=dict, tags=["AI - Functions List"])
async def regenerate_functions_list(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"functions-list/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/functions-list/regenerate-custom", summary="Regenerate FunctionsList Custom", response_model=dict, tags=["AI - Functions List"])
async def regenerate_custom_functions_list(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"functions-list/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/functions-list/chat", summary="Chat FunctionsList", response_model=dict, tags=["AI - Functions List"])
async def chat_functions_list(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"functions-list/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/functions-list/chat/stream", summary="Chat FunctionsList Stream", tags=["AI - Functions List"])
async def chat_stream_functions_list(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"functions-list/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: MVP-PLANNING
# ==========================================
@router.post("/mvp-planning", summary="Generate MvpPlanning", response_model=dict, tags=["AI - MVP Planning"])
async def generate_mvp_planning(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("mvp-planning", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/mvp-planning/regenerate", summary="Regenerate MvpPlanning", response_model=dict, tags=["AI - MVP Planning"])
async def regenerate_mvp_planning(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"mvp-planning/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/mvp-planning/regenerate-custom", summary="Regenerate MvpPlanning Custom", response_model=dict, tags=["AI - MVP Planning"])
async def regenerate_custom_mvp_planning(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"mvp-planning/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/mvp-planning/chat", summary="Chat MvpPlanning", response_model=dict, tags=["AI - MVP Planning"])
async def chat_mvp_planning(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"mvp-planning/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/mvp-planning/chat/stream", summary="Chat MvpPlanning Stream", tags=["AI - MVP Planning"])
async def chat_stream_mvp_planning(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"mvp-planning/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: UNIT-ECONOMICS
# ==========================================
@router.post("/unit-economics", summary="Generate UnitEconomics", response_model=dict, tags=["AI - Unit Economics"])
async def generate_unit_economics(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("unit-economics", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/unit-economics/regenerate", summary="Regenerate UnitEconomics", response_model=dict, tags=["AI - Unit Economics"])
async def regenerate_unit_economics(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"unit-economics/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/unit-economics/statements", summary="Generate Financial Statements", response_model=dict, tags=["AI - Unit Economics"])
async def generate_financial_statements(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    return await _forward_post_to_ai(f"unit-economics/{ai_user}/statements", payload=body, extra_headers=_ai_headers(current_user))

@router.post("/unit-economics/regenerate-custom", summary="Regenerate UnitEconomics Custom", response_model=dict, tags=["AI - Unit Economics"])
async def regenerate_custom_unit_economics(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"unit-economics/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/unit-economics/chat", summary="Chat UnitEconomics", response_model=dict, tags=["AI - Unit Economics"])
async def chat_unit_economics(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"unit-economics/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/unit-economics/chat/stream", summary="Chat UnitEconomics Stream", tags=["AI - Unit Economics"])
async def chat_stream_unit_economics(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"unit-economics/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: GO-TO-MARKET
# ==========================================
@router.post("/go-to-market", summary="Generate GoToMarket", response_model=dict, tags=["AI - Go To Market"])
async def generate_go_to_market(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("go-to-market", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/go-to-market/regenerate", summary="Regenerate GoToMarket", response_model=dict, tags=["AI - Go To Market"])
async def regenerate_go_to_market(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"go-to-market/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/go-to-market/regenerate-custom", summary="Regenerate GoToMarket Custom", response_model=dict, tags=["AI - Go To Market"])
async def regenerate_custom_go_to_market(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"go-to-market/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/go-to-market/chat", summary="Chat GoToMarket", response_model=dict, tags=["AI - Go To Market"])
async def chat_go_to_market(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"go-to-market/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/go-to-market/chat/stream", summary="Chat GoToMarket Stream", tags=["AI - Go To Market"])
async def chat_stream_go_to_market(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"go-to-market/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: AUDIT (cross-section Final Audit)
# ==========================================
@router.get("/audit", summary="Get Business Plan Audit", response_model=dict, tags=["AI - Audit"])
async def get_audit(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("audit", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))

@router.post("/audit", summary="Generate Business Plan Audit", response_model=dict, tags=["AI - Audit"])
async def generate_audit(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("audit", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/audit/regenerate", summary="Regenerate Business Plan Audit", response_model=dict, tags=["AI - Audit"])
async def regenerate_audit(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"audit/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/audit/regenerate-custom", summary="Regenerate Business Plan Audit Custom", response_model=dict, tags=["AI - Audit"])
async def regenerate_custom_audit(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"audit/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/audit/chat", summary="Chat Business Plan Audit", response_model=dict, tags=["AI - Audit"])
async def chat_audit(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"audit/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))


def _charge_section_credits(user_id, sections: list[str]) -> None:
    """Deduct the regen cost of each improved section (post-hoc, best-effort)."""
    total = sum(SECTION_CREDIT_COSTS.get(s, 0) for s in sections)
    if total <= 0:
        return
    try:
        db = SessionLocal()
        try:
            _usage_repo.deduct_credits(db, user_id, total)
        finally:
            db.close()
    except Exception:
        logger.warning("Failed to charge improve-section credits (sections=%s)", sections)


@router.post("/audit/improve-section", summary="Improve a flagged section using audit feedback", response_model=dict, tags=["AI - Audit"])
async def improve_audit_section(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    """
    Regenerate one section using the Final Audit's findings as the improvement
    brief. Returns before/after content for comparison. Charged at the
    section's normal regeneration cost.
    """
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {
        "section": payload.get("section"),
        "idea_id": payload.get("idea_id"),
        "settings_language": payload.get("settings_language", "en"),
    }
    result = await _forward_post_to_ai(
        f"audit/{ai_user}/improve-section", payload=body,
        extra_headers=_ai_headers(current_user), timeout=300,
    )
    if result.get("status") == "done" and result.get("section"):
        _charge_section_credits(current_user.id, [result["section"]])
    return result


@router.post("/audit/improve-all", summary="Improve every audit-flagged section", response_model=dict, tags=["AI - Audit"])
async def improve_all_audit_sections(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {
        "idea_id": payload.get("idea_id"),
        "settings_language": payload.get("settings_language", "en"),
    }
    result = await _forward_post_to_ai(
        f"audit/{ai_user}/improve-all", payload=body,
        extra_headers=_ai_headers(current_user), timeout=600,
    )
    improved = [item.get("section") for item in result.get("improved", []) if item.get("section")]
    if improved:
        _charge_section_credits(current_user.id, improved)
    return result


@router.get("/audit/flagged-sections", summary="Sections the audit flagged for improvement", response_model=dict, tags=["AI - Audit"])
async def get_audit_flagged_sections(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    ai_user = _resolve_ai_user_id(current_user, idea_id)
    return await _forward_get_to_ai(f"audit/{ai_user}/flagged-sections", "", params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))


@router.get("/audit/improvements", summary="Improvement version history", response_model=dict, tags=["AI - Audit"])
async def get_audit_improvements(
    current_user: User = Depends(get_current_user),
    idea_id: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
):
    ai_user = _resolve_ai_user_id(current_user, idea_id)
    params: dict[str, Any] = {}
    if idea_id:
        params["idea_id"] = idea_id
    if section:
        params["section"] = section
    return await _forward_get_to_ai(f"audit/{ai_user}/improvements", "", params=params or None, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: EXECUTION ROADMAP (Hero Execution Roadmap)
# ==========================================
@router.post("/roadmap/generate", summary="Generate Execution Roadmap", response_model=dict, tags=["AI - Roadmap"])
async def generate_roadmap(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    if payload.get("business_type"):
        body["business_type"] = payload["business_type"]
    if payload.get("language"):
        body["language"] = payload["language"]
    return await _forward_post_to_ai("roadmap", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None,
                                     extra_headers=_ai_headers(current_user))


@router.get("/roadmap", summary="Get Execution Roadmap", response_model=dict, tags=["AI - Roadmap"])
async def get_roadmap(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("roadmap", _resolve_ai_user_id(current_user, idea_id),
                                    params={"idea_id": idea_id} if idea_id else None,
                                    extra_headers=_ai_headers(current_user))


@router.get("/roadmap/status", summary="Get Roadmap Generation Status", response_model=dict, tags=["AI - Roadmap"])
async def get_roadmap_status(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai(f"roadmap/{_resolve_ai_user_id(current_user, idea_id)}/status", "",
                                    params={"idea_id": idea_id} if idea_id else None,
                                    extra_headers=_ai_headers(current_user))


@router.get("/roadmap/next-actions", summary="Get Roadmap Next Actions", response_model=dict, tags=["AI - Roadmap"])
async def get_roadmap_next_actions(current_user: User = Depends(get_current_user),
                                   idea_id: Optional[str] = Query(None), limit: int = Query(3, ge=1, le=10)):
    params: dict[str, Any] = {"limit": limit}
    if idea_id:
        params["idea_id"] = idea_id
    return await _forward_get_to_ai(f"roadmap/{_resolve_ai_user_id(current_user, idea_id)}/next-actions", "",
                                    params=params, extra_headers=_ai_headers(current_user))


@router.post("/roadmap/chat", summary="Execution Roadmap Coach Chat", response_model=dict, tags=["AI - Roadmap"])
async def chat_roadmap(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"roadmap/{ai_user}/chat", payload=payload,
                                     extra_headers=_ai_headers(current_user))


@router.patch("/roadmap/task/{task_id}/status", summary="Update Task Status", response_model=dict, tags=["AI - Roadmap"])
async def update_roadmap_task_status(task_id: str, payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    body = {"user_id": str(current_user.id), "status": payload.get("status")}
    return await _forward_write_to_ai("PATCH", f"roadmap/task/{task_id}/status", payload=body,
                                      extra_headers=_ai_headers(current_user))


@router.patch("/roadmap/task/{task_id}", summary="Edit Task", response_model=dict, tags=["AI - Roadmap"])
async def edit_roadmap_task(task_id: str, payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    body = {"user_id": str(current_user.id), "fields": payload.get("fields", {})}
    return await _forward_write_to_ai("PATCH", f"roadmap/task/{task_id}", payload=body,
                                      extra_headers=_ai_headers(current_user))


@router.delete("/roadmap/task/{task_id}", summary="Delete Task", response_model=dict, tags=["AI - Roadmap"])
async def delete_roadmap_task(task_id: str, current_user: User = Depends(get_current_user)):
    return await _forward_write_to_ai("DELETE", f"roadmap/task/{task_id}",
                                      params={"user_id": str(current_user.id)},
                                      extra_headers=_ai_headers(current_user))


@router.patch("/roadmap/subtask/{subtask_id}", summary="Update Subtask", response_model=dict, tags=["AI - Roadmap"])
async def update_roadmap_subtask(subtask_id: str, payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {"user_id": str(current_user.id)}
    if payload.get("status") is not None:
        body["status"] = payload["status"]
    if payload.get("action_items") is not None:
        body["action_items"] = payload["action_items"]
    return await _forward_write_to_ai("PATCH", f"roadmap/subtask/{subtask_id}", payload=body,
                                      extra_headers=_ai_headers(current_user))


@router.post("/roadmap/task", summary="Add Custom Task", response_model=dict, tags=["AI - Roadmap"])
async def add_roadmap_custom_task(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    body = {
        "user_id": str(current_user.id),
        "milestone_id": payload.get("milestone_id"),
        "fields": payload.get("fields", {}),
    }
    return await _forward_post_to_ai("roadmap/task", payload=body, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: MARKETING — Customer Research
# ==========================================
@router.get("/customer-research", summary="Get Customer Research", response_model=dict, tags=["AI - Marketing"])
async def get_customer_research(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("customer-research", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))

@router.post("/customer-research", summary="Generate Customer Research", response_model=dict, tags=["AI - Marketing"])
async def generate_customer_research(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("customer-research", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/customer-research/regenerate", summary="Regenerate Customer Research", response_model=dict, tags=["AI - Marketing"])
async def regenerate_customer_research(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"customer-research/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/customer-research/regenerate-custom", summary="Regenerate Customer Research Custom", response_model=dict, tags=["AI - Marketing"])
async def regenerate_custom_customer_research(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"customer-research/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/customer-research/chat", summary="Chat Customer Research", response_model=dict, tags=["AI - Marketing"])
async def chat_customer_research(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"customer-research/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/customer-research/chat/stream", summary="Chat Customer Research Stream", tags=["AI - Marketing"])
async def chat_stream_customer_research(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"customer-research/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: MARKETING — Copywriting
# ==========================================
@router.get("/copywriting", summary="Get Copywriting", response_model=dict, tags=["AI - Marketing"])
async def get_copywriting(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("copywriting", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))

@router.post("/copywriting", summary="Generate Copywriting", response_model=dict, tags=["AI - Marketing"])
async def generate_copywriting(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("copywriting", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/copywriting/regenerate", summary="Regenerate Copywriting", response_model=dict, tags=["AI - Marketing"])
async def regenerate_copywriting(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"copywriting/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/copywriting/regenerate-custom", summary="Regenerate Copywriting Custom", response_model=dict, tags=["AI - Marketing"])
async def regenerate_custom_copywriting(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"copywriting/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/copywriting/chat", summary="Chat Copywriting", response_model=dict, tags=["AI - Marketing"])
async def chat_copywriting(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"copywriting/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/copywriting/chat/stream", summary="Chat Copywriting Stream", tags=["AI - Marketing"])
async def chat_stream_copywriting(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"copywriting/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: MARKETING — Pricing
# ==========================================
@router.get("/marketing-pricing", summary="Get Marketing Pricing", response_model=dict, tags=["AI - Marketing"])
async def get_marketing_pricing(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("marketing-pricing", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))

@router.post("/marketing-pricing", summary="Generate Marketing Pricing", response_model=dict, tags=["AI - Marketing"])
async def generate_marketing_pricing(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("marketing-pricing", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/marketing-pricing/regenerate", summary="Regenerate Marketing Pricing", response_model=dict, tags=["AI - Marketing"])
async def regenerate_marketing_pricing(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"marketing-pricing/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/marketing-pricing/regenerate-custom", summary="Regenerate Marketing Pricing Custom", response_model=dict, tags=["AI - Marketing"])
async def regenerate_custom_marketing_pricing(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"marketing-pricing/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/marketing-pricing/chat", summary="Chat Marketing Pricing", response_model=dict, tags=["AI - Marketing"])
async def chat_marketing_pricing(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"marketing-pricing/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/marketing-pricing/chat/stream", summary="Chat Marketing Pricing Stream", tags=["AI - Marketing"])
async def chat_stream_marketing_pricing(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"marketing-pricing/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: MARKETING — Launch Strategy
# ==========================================
@router.get("/launch-strategy", summary="Get Launch Strategy", response_model=dict, tags=["AI - Marketing"])
async def get_launch_strategy(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("launch-strategy", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))

@router.post("/launch-strategy", summary="Generate Launch Strategy", response_model=dict, tags=["AI - Marketing"])
async def generate_launch_strategy(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("launch-strategy", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/launch-strategy/regenerate", summary="Regenerate Launch Strategy", response_model=dict, tags=["AI - Marketing"])
async def regenerate_launch_strategy(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"launch-strategy/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/launch-strategy/regenerate-custom", summary="Regenerate Launch Strategy Custom", response_model=dict, tags=["AI - Marketing"])
async def regenerate_custom_launch_strategy(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"launch-strategy/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/launch-strategy/chat", summary="Chat Launch Strategy", response_model=dict, tags=["AI - Marketing"])
async def chat_launch_strategy(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"launch-strategy/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/launch-strategy/chat/stream", summary="Chat Launch Strategy Stream", tags=["AI - Marketing"])
async def chat_stream_launch_strategy(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"launch-strategy/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: MARKETING — Ad Creative
# ==========================================
@router.get("/ad-creative", summary="Get Ad Creative", response_model=dict, tags=["AI - Marketing"])
async def get_ad_creative(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("ad-creative", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))

@router.post("/ad-creative", summary="Generate Ad Creative", response_model=dict, tags=["AI - Marketing"])
async def generate_ad_creative(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("ad-creative", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/ad-creative/regenerate", summary="Regenerate Ad Creative", response_model=dict, tags=["AI - Marketing"])
async def regenerate_ad_creative(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"ad-creative/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/ad-creative/regenerate-custom", summary="Regenerate Ad Creative Custom", response_model=dict, tags=["AI - Marketing"])
async def regenerate_custom_ad_creative(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"ad-creative/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/ad-creative/chat", summary="Chat Ad Creative", response_model=dict, tags=["AI - Marketing"])
async def chat_ad_creative(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"ad-creative/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/ad-creative/chat/stream", summary="Chat Ad Creative Stream", tags=["AI - Marketing"])
async def chat_stream_ad_creative(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"ad-creative/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: MARKETING — Social Media
# ==========================================
@router.get("/social-media", summary="Get Social Media Strategy", response_model=dict, tags=["AI - Marketing"])
async def get_social_media(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("social-media", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))

@router.post("/social-media", summary="Generate Social Media Strategy", response_model=dict, tags=["AI - Marketing"])
async def generate_social_media(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("social-media", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/social-media/regenerate", summary="Regenerate Social Media Strategy", response_model=dict, tags=["AI - Marketing"])
async def regenerate_social_media(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"social-media/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/social-media/regenerate-custom", summary="Regenerate Social Media Custom", response_model=dict, tags=["AI - Marketing"])
async def regenerate_custom_social_media(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"social-media/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/social-media/chat", summary="Chat Social Media", response_model=dict, tags=["AI - Marketing"])
async def chat_social_media(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"social-media/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/social-media/chat/stream", summary="Chat Social Media Stream", tags=["AI - Marketing"])
async def chat_stream_social_media(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"social-media/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ==========================================
# Domain: MARKETING — Marketing Ideas
# ==========================================
@router.get("/marketing-ideas", summary="Get Marketing Ideas", response_model=dict, tags=["AI - Marketing"])
async def get_marketing_ideas(current_user: User = Depends(get_current_user), idea_id: Optional[str] = Query(None)):
    return await _forward_get_to_ai("marketing-ideas", _resolve_ai_user_id(current_user, idea_id), params={"idea_id": idea_id} if idea_id else None, extra_headers=_ai_headers(current_user))

@router.post("/marketing-ideas", summary="Generate Marketing Ideas", response_model=dict, tags=["AI - Marketing"])
async def generate_marketing_ideas(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    body: dict[str, Any] = {}
    if payload.get("idea_id"):
        body["idea_id"] = payload["idea_id"]
    return await _forward_post_to_ai("marketing-ideas", _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True), payload=body or None, extra_headers=_ai_headers(current_user))

@router.post("/marketing-ideas/regenerate", summary="Regenerate Marketing Ideas", response_model=dict, tags=["AI - Marketing"])
async def regenerate_marketing_ideas(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    body = {"idea_id": payload["idea_id"]} if payload.get("idea_id") else None
    return await _forward_post_to_ai(f"marketing-ideas/{ai_user}/regenerate", None, payload=body, extra_headers=_ai_headers(current_user))

@router.post("/marketing-ideas/regenerate-custom", summary="Regenerate Marketing Ideas Custom", response_model=dict, tags=["AI - Marketing"])
async def regenerate_custom_marketing_ideas(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"), require_edit=True)
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"marketing-ideas/{ai_user}/regenerate-custom", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/marketing-ideas/chat", summary="Chat Marketing Ideas", response_model=dict, tags=["AI - Marketing"])
async def chat_marketing_ideas(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_post_to_ai(f"marketing-ideas/{ai_user}/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/marketing-ideas/chat/stream", summary="Chat Marketing Ideas Stream", tags=["AI - Marketing"])
async def chat_stream_marketing_ideas(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    ai_user = _resolve_ai_user_id(current_user, payload.get("idea_id"))
    payload["user_id"] = ai_user
    return await _forward_stream_to_ai(f"marketing-ideas/{ai_user}/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

# ─── PDF Validation (forwards to AI service /pipeline/validate/...) ───────────
_VALIDATION_TIMEOUT_SECONDS = 240  # validation runs web search + multiple LLM calls


@router.get(
    "/validate/result/{validation_id}",
    summary="Get Validation Result",
    response_model=dict,
    tags=["AI - Validation"],
)
async def get_validation_result(
    validation_id: str,
    current_user: User = Depends(get_current_user),
):
    # AI route is /pipeline/validate/result/{validation_id} (no user_id segment).
    # Forward the authenticated user id so the AI service can enforce ownership.
    return await _forward_get_to_ai(
        f"validate/result/{validation_id}", "", params={"user_id": str(current_user.id)},
        extra_headers=_ai_headers(current_user),
    )


@router.get(
    "/validate/{section}",
    summary="List Section Validations",
    response_model=dict,
    tags=["AI - Validation"],
)
async def list_section_validations(
    section: str,
    idea_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    params = {"idea_id": idea_id} if idea_id else None
    return await _forward_get_to_ai(f"validate/{section}", str(current_user.id), params=params, extra_headers=_ai_headers(current_user))


@router.post(
    "/validate/{section}",
    summary="Validate Section PDF",
    response_model=dict,
    tags=["AI - Validation"],
)
async def validate_section_pdf(
    section: str,
    file: UploadFile = File(...),
    validation_mode: str = Form("generic"),
    idea_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/validate/{section}/{current_user.id}"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY}

    # Cap the upload so a large file can't exhaust backend memory before the AI
    # service rejects it. Read MAX+1 to detect overflow without loading more.
    _MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB (matches AI service limit)
    file_bytes = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="PDF file is too large. Maximum size is 15 MB.",
        )
    files = {"file": (file.filename or "document.pdf", file_bytes, file.content_type or "application/pdf")}
    data: dict[str, str] = {"validation_mode": validation_mode}
    if idea_id:
        data["idea_id"] = idea_id

    try:
        async with httpx.AsyncClient(timeout=_VALIDATION_TIMEOUT_SECONDS) as client:
            response = await client.post(target_url, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise _http_exception_from_upstream(exc.response)
    except httpx.RequestError as exc:
        logger.error("AI validate request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


@_system_router.get("/health", summary="Health", tags=["AI - System"])
async def get_health():
    return await _forward_get_to_ai("health", "")

@_system_router.get("/version-check", summary="Version Check", tags=["AI - System"])
async def get_version_check():
    return await _forward_get_to_ai("version-check", "")

@router.get("/questionnaire", summary="Get Questionnaire", tags=["AI - Profile"])
async def get_questionnaire(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("questionnaire", str(current_user.id), extra_headers=_ai_headers(current_user))

@router.post("/rerun/profile", summary="Rerun Profile", tags=["AI - Profile"])
async def rerun_profile(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai("rerun/profile", str(current_user.id), extra_headers=_ai_headers(current_user))

@router.post("/rerun/problems", summary="Rerun Problems", tags=["AI - Problems"])
async def rerun_problems(current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai("rerun/problems", str(current_user.id), extra_headers=_ai_headers(current_user))

@router.post("/idea-intake", summary="Idea Intake", tags=["AI - Idea Intake"])
async def idea_intake(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai("idea-intake", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/idea-intake/run-problems", summary="Idea Intake Run Problems", tags=["AI - Idea Intake"])
async def idea_intake_run_problems(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    return await _forward_post_to_ai(f"idea-intake/run-problems/{current_user.id}", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/idea-intake/start-chat", summary="Idea Intake Start Chat", tags=["AI - Idea Intake"])
async def idea_intake_start_chat(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai("idea-intake/start-chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/idea-intake/chat", summary="Idea Intake Chat (Phase B)", tags=["AI - Idea Intake"])
async def idea_intake_chat(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai("idea-intake/chat", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/idea-intake/chat/stream", summary="Idea Intake Chat Stream", tags=["AI - Idea Intake"])
async def idea_intake_chat_stream(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_stream_to_ai("idea-intake/chat/stream", payload=payload, extra_headers=_ai_headers(current_user))

@router.get("/idea-intake", summary="Get Idea Intake", tags=["AI - Idea Intake"])
async def get_idea_intake(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("idea-intake", str(current_user.id), extra_headers=_ai_headers(current_user))

@router.get("/idea-intake/draft", summary="Get Idea Draft (pre-approval)", tags=["AI - Idea Intake"])
async def get_idea_draft(current_user: User = Depends(get_current_user)):
    return await _forward_get_to_ai("idea-intake/draft", str(current_user.id), extra_headers=_ai_headers(current_user))

@router.post("/idea-intake/approve", summary="Approve Idea Draft", tags=["AI - Idea Intake"])
async def idea_intake_approve(payload: dict[str, Any] = {}, current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai("idea-intake/approve", payload=payload, extra_headers=_ai_headers(current_user))

@router.post("/idea-intake/manual", summary="Manual Idea Create (enriched)", tags=["AI - Idea Intake"])
async def idea_intake_manual(payload: dict[str, Any], current_user: User = Depends(get_current_user)):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai("idea-intake/manual", payload=payload, extra_headers=_ai_headers(current_user))


@router.get(
    "/ideas/{idea_id}/partner-suggestions",
    summary="Get supplier/manufacturer suggestions for an idea",
    tags=["AI - Pipeline"],
)
async def get_partner_suggestions(
    idea_id: UUID,
    current_user: User = Depends(get_current_user),
    limit: int = Query(5, ge=1, le=20),
) -> dict[str, Any]:
    """Proxy to bizifyAI: returns keyword-matched supplier and manufacturer suggestions for an idea."""
    if not settings.AI_PIPELINE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI_PIPELINE_API_KEY not configured on server.",
        )
    target_url = f"{_AI_BASE_URL}/pipeline/partners/suggest-for-idea"
    headers = {"x-api-key": settings.AI_PIPELINE_API_KEY}
    params = {"idea_id": str(idea_id), "user_id": str(current_user.id), "limit": limit}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(target_url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise _http_exception_from_upstream(exc.response)
    except httpx.RequestError as exc:
        logger.error("AI partner suggestions request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Service unavailable.")


@router.post("/ideas/{idea_id}/seed-context", summary="Seed Idea Context in BizifyAI", tags=["AI - Pipeline"])
async def seed_idea_context(
    idea_id: UUID,
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    payload["user_id"] = str(current_user.id)
    return await _forward_post_to_ai(f"idea/{idea_id}/seed-context", payload=payload, extra_headers=_ai_headers(current_user))


@router.delete("/ideas/{idea_id}/analysis", status_code=204, summary="Clear Idea Analysis", tags=["AI - Pipeline"])
async def clear_idea_analysis(
    idea_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = str(current_user.id)
    iid = str(idea_id)
    for table in [
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
