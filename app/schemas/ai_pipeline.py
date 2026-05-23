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
    tokens_used: Optional[int] = None

# --- New AI Pipeline Response Models ---

class AIPipelineStatusResponse(BaseModel):
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
    user_id: Optional[str] = None
    current_step: Optional[str] = None
    error: Optional[str] = None
    profile_ready: Optional[bool] = None
    problems_ready: Optional[bool] = None
    intake_ready: Optional[bool] = None
    idea_ready: Optional[bool] = None
    customers_ready: Optional[bool] = None
    competition_ready: Optional[bool] = None
    market_potential_ready: Optional[bool] = None
    idea_strategy_ready: Optional[bool] = None
    business_model_ready: Optional[bool] = None
    functions_list_ready: Optional[bool] = None
    mvp_planning_ready: Optional[bool] = None
    unit_economics_ready: Optional[bool] = None
    go_to_market_ready: Optional[bool] = None
    pipeline_complete: Optional[bool] = None

class AIProfileResponse(BaseModel):
    profile_analysis: dict[str, Any]

class AICustomersResponse(BaseModel):
    customers: list[dict[str, Any]]

class AICompetitionResponse(BaseModel):
    competition: dict[str, Any]

class AIMarketPotentialResponse(BaseModel):
    market_potential: dict[str, Any]

class AIIdeaStrategyResponse(BaseModel):
    idea_strategy: dict[str, Any]

class AIBusinessModelResponse(BaseModel):
    business_model: dict[str, Any]

class AIFunctionsListResponse(BaseModel):
    functions_list: dict[str, Any]

class AIMVPPlanningResponse(BaseModel):
    mvp_planning: dict[str, Any]

class AIUnitEconomicsResponse(BaseModel):
    unit_economics: dict[str, Any]

class AIGoToMarketResponse(BaseModel):
    go_to_market: dict[str, Any]

class AIProblemsResponse(BaseModel):
    # The AI service returns the full problems result object (dict), not a list.
    # Shape: {"problems": [...], "customer_segments": [...], "source_mode": "..."}
    problems: dict[str, Any]

class AIIdeaResponse(BaseModel):
    # current_idea is plain formatted text, not a JSON object.
    current_idea: str
    chat_history: Optional[list] = None
