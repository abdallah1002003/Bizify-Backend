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
