from typing import Any, Optional

from pydantic import BaseModel


class AIPipelineRequest(BaseModel):
    """
    Request payload forwarded to the external AI pipeline.
    The 'data' field is intentionally flexible (Any) until the
    pipeline contract is finalised by the AI team.
    """

    data: Optional[Any] = None


class AIPipelineResponse(BaseModel):
    """
    Response returned from the external AI pipeline.
    """

    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class GeneralChatRequest(BaseModel):
    """Request schema for the General Chatbot."""

    message: str
    history: list[dict[str, Any]] = []


class GeneralChatResponse(BaseModel):
    """Response schema for the General Chatbot."""

    reply: str
    intent: Optional[str] = None
    section: Optional[str] = None
    action: Optional[str] = None
    route_to_trigger: Optional[str] = None
    trigger_needed: Optional[bool] = None
    chat_history_length: Optional[int] = None
