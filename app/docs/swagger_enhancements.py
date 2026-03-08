"""
Swagger/OpenAPI Enhancement Guide for Bizify API

This module provides guidelines and utilities for improving API documentation.
Apply the patterns shown here to all routes for comprehensive API documentation.

Example patterns:
- Add descriptions and examples to request/response models
- Use Response models for 200, 400, 401, 403, 404, 422, 500 status codes
- Add tags and summaries to endpoints
"""

from typing import Optional
from pydantic import BaseModel, Field

# ============================================================================
# Common Response Models for Consistency
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response structure."""
    error_code: str = Field(
        ..., 
        description="Machine-readable error code (e.g., CONFLICT, VALIDATION_ERROR)"
    )
    message: str = Field(
        ..., 
        description="Human-readable error message"
    )
    status_code: int = Field(
        ..., 
        description="HTTP status code"
    )
    details: Optional[dict] = Field(
        None,
        description="Additional error details (e.g., validation errors)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "status_code": 422,
                "details": {
                    "field": "email",
                    "constraint": "unique"
                }
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response."""
    status_code: int = Field(..., description="HTTP status code (2xx)")
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": 200,
                "message": "Operation successful",
                "data": {}
            }
        }


# ============================================================================
# Common Response Examples for Different Endpoints
# ============================================================================

# User endpoints standard responses
USER_ENDPOINT_RESPONSES = {
    400: {
        "description": "Invalid request",
        "model": ErrorResponse,
    },
    401: {
        "description": "Unauthorized - missing or invalid authentication token",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "UNAUTHORIZED",
                    "message": "Invalid or expired authentication token",
                    "status_code": 401
                }
            }
        }
    },
    403: {
        "description": "Forbidden - insufficient permissions",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "FORBIDDEN",
                    "message": "You do not have permission to access this resource",
                    "status_code": 403
                }
            }
        }
    },
    404: {
        "description": "Resource not found",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "NOT_FOUND",
                    "message": "User not found",
                    "status_code": 404
                }
            }
        }
    },
    422: {
        "description": "Validation error",
        "model": ErrorResponse,
    },
    429: {
        "description": "Rate limit exceeded",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "status_code": 429
                }
            }
        }
    },
    500: {
        "description": "Internal server error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "status_code": 500
                }
            }
        }
    }
}

BUSINESS_ENDPOINT_RESPONSES = {
    **USER_ENDPOINT_RESPONSES,
    409: {
        "description": "Conflict - business already exists or constraint violation",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "CONFLICT",
                    "message": "Business with this name already exists",
                    "status_code": 409
                }
            }
        }
    }
}

BILLING_ENDPOINT_RESPONSES = {
    **USER_ENDPOINT_RESPONSES,
    402: {
        "description": "Payment required",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "PAYMENT_REQUIRED",
                    "message": "Subscription required for this operation",
                    "status_code": 402
                }
            }
        }
    }
}

# ============================================================================
# OpenAPI Tags
# ============================================================================

TAGS_METADATA = [
    {
        "name": "users",
        "description": "User registration, authentication, and profile management"
    },
    {
        "name": "auth",
        "description": "Authentication endpoints (login, logout, token refresh)"
    },
    {
        "name": "businesses",
        "description": "Business operations (create, read, update, delete, collaborate)"
    },
    {
        "name": "ideas",
        "description": "Idea management (create, versions, metrics, comparisons)"
    },
    {
        "name": "chat",
        "description": "Chat sessions and messaging with AI"
    },
    {
        "name": "billing",
        "description": "Plans, subscriptions, payments, and usage tracking"
    },
    {
        "name": "partners",
        "description": "Partner profiles and partnership requests"
    },
    {
        "name": "ai",
        "description": "AI agents, runs, and embeddings"
    },
]

# ============================================================================
# Implementation Checklist
# ============================================================================

"""
To implement comprehensive Swagger documentation for all endpoints:

1. USER ENDPOINTS (/api/v1/users/):
   ☐ POST /users/ - Create user
   ☐ GET /users/me - Get current user profile
   ☐ GET /users/{user_id} - Get user by ID
   ☐ PUT /users/{user_id} - Update user
   ☐ DELETE /users/{user_id} - Delete user
   ☐ GET /users/{user_id}/profile - Get detailed profile
   ☐ PUT /users/{user_id}/profile - Update profile

2. AUTH ENDPOINTS (/api/v1/auth/):
   ☐ POST /auth/login - User login
   ☐ POST /auth/logout - User logout
   ☐ POST /auth/refresh-token - Refresh JWT token
   ☐ POST /auth/bootstrap-admin - Create initial admin (protected)

3. BUSINESS ENDPOINTS (/api/v1/businesses/):
   ☐ POST /businesses/ - Create business
   ☐ GET /businesses/ - List businesses
   ☐ GET /businesses/{business_id} - Get business details
   ☐ PUT /businesses/{business_id} - Update business
   ☐ DELETE /businesses/{business_id} - Delete business
   ☐ POST /businesses/{business_id}/collaborators - Add collaborator
   ☐ GET /businesses/{business_id}/collaborators - List collaborators
   ☐ DELETE /businesses/{business_id}/collaborators/{user_id} - Remove collaborator

4. IDEA ENDPOINTS (/api/v1/ideas/):
   ☐ POST /ideas/ - Create idea
   ☐ GET /ideas/ - List ideas (paginated)
   ☐ GET /ideas/{idea_id} - Get idea details
   ☐ PUT /ideas/{idea_id} - Update idea
   ☐ DELETE /ideas/{idea_id} - Delete idea
   ☐ POST /ideas/{idea_id}/versions - Create version
   ☐ GET /ideas/{idea_id}/versions - List versions
   ☐ POST /ideas/{idea_id}/metrics - Add metric
   ☐ GET /ideas/{idea_id}/metrics - Get metrics

5. BILLING ENDPOINTS (/api/v1/billing/):
   ☐ GET /plans/ - List plans
   ☐ GET /plans/{plan_id} - Get plan details
   ☐ POST /subscriptions/ - Create subscription
   ☐ GET /subscriptions/ - List user subscriptions
   ☐ GET /subscriptions/{sub_id} - Get subscription details
   ☐ PUT /subscriptions/{sub_id} - Update subscription
   ☐ POST /payments/ - Create payment
   ☐ GET /payments/{payment_id} - Get payment details

6. PARTNER ENDPOINTS (/api/v1/partners/):
   ☐ POST /partner-profiles/ - Create profile
   ☐ GET /partner-profiles/ - List profiles (filterable)
   ☐ GET /partner-profiles/{profile_id} - Get profile
   ☐ PUT /partner-profiles/{profile_id} - Update profile
   ☐ POST /partner-requests/ - Create request
   ☐ GET /partner-requests/ - List requests
   ☐ POST /partner-requests/{request_id}/accept - Accept request
   ☐ POST /partner-requests/{request_id}/reject - Reject request

7. CHAT ENDPOINTS (/api/v1/chat/):
   ☐ POST /chat-sessions/ - Create session
   ☐ GET /chat-sessions/{session_id} - Get session
   ☐ POST /chat-messages/ - Send message
   ☐ GET /chat-sessions/{session_id}/messages - Get messages

For each endpoint, add:
   - Clear description of what it does
   - Request body examples
   - Response examples for all status codes
   - Error descriptions
   - Required authentication/permissions
   - Rate limit info
"""

# ============================================================================
# Usage Example
# ============================================================================

# In your routes file, import and use:
# from app.docs.swagger_enhancements import (
#     USER_ENDPOINT_RESPONSES,
#     BUSINESS_ENDPOINT_RESPONSES,
#     TAGS_METADATA,
# )
#
# Then in main.py:
# app = FastAPI(
#     ...,
#     openapi_tags=TAGS_METADATA,
# )
#
# And in your routes:
# @router.post(
#     "/users/",
#     response_model=UserResponse,
#     tags=["users"],
#     summary="Create a new user",
#     responses=USER_ENDPOINT_RESPONSES,
# )
