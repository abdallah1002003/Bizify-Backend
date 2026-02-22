"""Pagination utilities shared by API endpoints."""

from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, Field

# Reusable typed query parameters for paginated list endpoints.
SkipParam = Annotated[int, Query(ge=0, description="Number of records to skip")]
LimitParam = Annotated[int, Query(ge=1, le=100, description="Number of records to return (max 100)")]


class PaginationParams(BaseModel):
    """Normalized pagination values used by services."""

    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of records to return (max 100)")


def get_pagination_params(skip: SkipParam = 0, limit: LimitParam = 20) -> tuple[int, int]:
    """Return validated `(skip, limit)` values for callers using tuple semantics."""

    return skip, limit
