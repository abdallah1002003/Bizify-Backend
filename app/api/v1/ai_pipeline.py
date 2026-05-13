import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.ai_pipeline import GeneralChatRequest, GeneralChatResponse
from app.services.ai_pipeline_service import AIPipelineService

logger = logging.getLogger(__name__)

router = APIRouter()

_AI_BASE_URL = "https://bizifyai-production.up.railway.app"
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


@router.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    summary="AI Pipeline Generic Proxy",
    include_in_schema=False,
    description=(
        "A secure, authenticated proxy that forwards any request to the AI pipeline service. "
        "Validates the user's JWT token, injects the x-api-key, and overrides the user_id "
        "with the authenticated user's ID to prevent unauthorized access to other users' data."
    ),
)
async def ai_pipeline_proxy(
    full_path: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Generic proxy to the external AI pipeline service.

    Security guarantees:
    - JWT must be valid (enforced by get_current_user dependency).
    - x-api-key is injected server-side (never exposed to the client).
    - user_id in the request body is always overridden with the authenticated user's ID.
    - user_id path params are validated to match the authenticated user's ID.
    """
    user_id = str(current_user.id)

    path_parts = full_path.split("/")
    for i, part in enumerate(path_parts):
        if i > 0 and part and part != user_id:
            prev = path_parts[i - 1] if i > 0 else ""
            known_resources = {
                "status", "idea", "questionnaire", "profile", "problems",
                "idea-intake", "customers", "competition", "market-potential", "idea-strategy"
            }
            if prev in known_resources:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not allowed to access another user's pipeline data.",
                )

    target_url = f"{_AI_BASE_URL}/pipeline/{full_path}"

    forwarded_headers = {
        "x-api-key": settings.AI_PIPELINE_API_KEY,
        "Content-Type": "application/json",
    }

    body_bytes = await request.body()
    body: dict | None = None

    if body_bytes:
        import json
        try:
            body = json.loads(body_bytes)
            if isinstance(body, dict):
                body["user_id"] = user_id
        except (json.JSONDecodeError, ValueError):
            body = None

    try:
        client = httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS)
        
        req = client.build_request(
            method=request.method,
            url=target_url,
            headers=forwarded_headers,
            json=body if body is not None else None,
            content=body_bytes if body is None and body_bytes else None,
            params=dict(request.query_params),
        )

        logger.info(
            "Proxying %s /pipeline/%s for user %s",
            request.method, full_path, user_id,
        )

        proxy_response = await client.send(req, stream=True)

        if proxy_response.is_error:
            await proxy_response.aread()
            error_text = proxy_response.text
            await proxy_response.aclose()
            await client.aclose()
            logger.error("AI pipeline returned HTTP %s: %s", proxy_response.status_code, error_text)
            raise HTTPException(
                status_code=proxy_response.status_code,
                detail=f"AI pipeline error: {error_text}",
            )

        logger.info(
            "AI pipeline responded %s for /pipeline/%s. Starting stream...",
            proxy_response.status_code, full_path,
        )

        async def stream_generator():
            try:
                async for chunk in proxy_response.aiter_bytes():
                    yield chunk
            finally:
                await proxy_response.aclose()
                await client.aclose()

        return StreamingResponse(
            stream_generator(),
            status_code=proxy_response.status_code,
            headers={"Content-Type": proxy_response.headers.get("content-type", "text/event-stream")},
        )

    except httpx.TimeoutException:
        logger.error("AI pipeline request timed out for /pipeline/%s", full_path)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI pipeline is taking too long to respond. Please try again.",
        ) from None
    except httpx.HTTPStatusError as exc:
        logger.error("AI pipeline returned HTTP %s: %s", exc.response.status_code, exc.response.text)
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"AI pipeline error: {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("AI pipeline request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the AI pipeline. Please try again later.",
        ) from exc
