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

# --- New AI Pipeline Response Models ---

class AIPipelineStatusResponse(BaseModel):
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None

class AIProfileResponse(BaseModel):
    profile_analysis: dict[str, Any]

class AICustomersResponse(BaseModel):
    customers: list[dict[str, Any]]

class AICompetitionResponse(BaseModel):
    competitors: list[dict[str, Any]]

class AIMarketPotentialResponse(BaseModel):
    market_potential: dict[str, Any]

class AIIdeaStrategyResponse(BaseModel):
    strategy: dict[str, Any]

class AIBusinessModelResponse(BaseModel):
    business_model: dict[str, Any]

class AIFunctionsListResponse(BaseModel):
    functions: list[dict[str, Any]]

class AIMVPPlanningResponse(BaseModel):
    mvp: dict[str, Any]

class AIUnitEconomicsResponse(BaseModel):
    economics: dict[str, Any]

class AIGoToMarketResponse(BaseModel):
    go_to_market: dict[str, Any]

class AIProblemsResponse(BaseModel):
    problems: list[dict[str, Any]]

class AIIdeaResponse(BaseModel):
    current_idea: dict[str, Any]
    score: Optional[float] = None
