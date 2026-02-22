"""Pagination utilities for API endpoints."""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Standard pagination query parameters."""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of records to return (max 100)")


def get_pagination_params(skip: int = 0, limit: int = 20) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        skip: Number of records to skip (default 0)
        limit: Number of records to return (default 20, max 100)
        
    Returns:
        Tuple of (skip, limit) with validated values
    """
    skip = max(0, skip)
    limit = max(1, min(limit, 100))  # Clamp between 1 and 100
    return skip, limit
