"""
Pagination utilities and types for API endpoints.

This module provides:
    - Reusable FastAPI query parameter types for pagination
    - Standardized pagination response models
    - Helper functions for extracting pagination parameters
    - Generic response envelope for paginated results
    
All paginated endpoints should use PaginationParams and PageResponse
for consistency across the API.
"""

from typing import Annotated, Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

# Reusable typed query parameters for paginated list endpoints.
SkipParam = Annotated[int, Query(ge=0, description="Number of records to skip")]
"""
Query parameter type for pagination skip (offset).

- Minimum value: 0
- Used in endpoint signatures to enforce validation
- Automatically validates that skip >= 0

Example:
    >>> @app.get("/items")
    >>> def list_items(skip: SkipParam = 0, limit: LimitParam = 20):
    ...     pass
"""

LimitParam = Annotated[int, Query(ge=1, le=100, description="Number of records to return (max 100)")]
"""
Query parameter type for pagination limit (page size).

- Minimum value: 1
- Maximum value: 100 (prevents abuse)
- Used in endpoint signatures to enforce validation
- Automatically validates that 1 <= limit <= 100

Example:
    >>> @app.get("/items")
    >>> def list_items(skip: SkipParam = 0, limit: LimitParam = 20):
    ...     pass
"""


class PaginationParams(BaseModel):
    """
    Normalized pagination values used by services.
    
    Provides consistent pagination parameters for internal service operations.
    All values are pre-validated to ensure database queries are safe.
    
    Attributes:
        skip: Number of records to skip (offset). Non-negative integer.
        limit: Number of records to return (page size). Between 1 and 100.
        
    Example:
        >>> params = PaginationParams(skip=10, limit=50)
        >>> items = service.list_with_pagination(db, params)
    """

    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of records to return (max 100)")


T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """
    Generic paginated response with total count.
    
    Standard envelope for any paginated API response. Provides both the items
    on the current page and total count for client-side pagination UI.
    
    Type Parameters:
        T: Type of items in this response (e.g., UserResponse, IdeaResponse)
    
    Attributes:
        items: List of items on this page
        total: Total number of items across all pages
        skip: Number of records skipped (offset used)
        limit: Number of records on this page (page size)
        
    Example:
        >>> response = PageResponse[UserResponse](
        ...     items=[user1, user2],
        ...     total=1000,
        ...     skip=0,
        ...     limit=20
        ... )
        >>> # Serializes to:
        >>> # {
        >>> #   "items": [...],
        >>> #   "total": 1000,
        >>> #   "skip": 0,
        >>> #   "limit": 20
        >>> # }
    """
    items: List[T]
    total: int = Field(..., ge=0, description="Total number of records")
    skip: int = Field(0, ge=0, description="Number of records skipped")
    limit: int = Field(20, ge=1, le=100, description="Number of records returned")


def get_pagination_params(skip: SkipParam = 0, limit: LimitParam = 20) -> tuple[int, int]:
    """
    Extract and validate pagination parameters from route arguments.
    
    Convenience function for routes that need to pass pagination params to services.
    Automatically validates skip and limit through type annotations.
    
    Args:
        skip: Number of records to skip (skip >= 0)
        limit: Number of records to return (1 <= limit <= 100)
    
    Returns:
        Tuple of (skip, limit) ready to pass to service layer
        
    Example:
        >>> @app.get("/items")
        >>> def list_items(skip: SkipParam = 0, limit: LimitParam = 20):
        ...     skip, limit = get_pagination_params(skip, limit)
        ...     items = service.list_items(db, skip=skip, limit=limit)
        ...     return items
        
    Note:
        - Validation happens via type annotations before this function is called
        - Always returns a valid tuple
        - No additional validation needed in this function
    """
    return skip, limit


