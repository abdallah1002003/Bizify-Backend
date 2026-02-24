"""
Pydantic schemas for user-related API requests and responses.

Defines the structure and validation for:
    - UserCreate: User registration payload
    - UserUpdate: User profile modification payload
    - UserResponse: User information returned from API

All schemas use Pydantic BaseModel for automatic validation and serialization.
"""

from app.models.enums import UserRole
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic import EmailStr
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    """
    Base schema containing common user fields.
    
    Used as a foundation for other user schemas to ensure consistent
    field definitions across Create, Update, and Response schemas.
    
    Attributes:
        name: Full name of the user (2-100 chars, alphanumeric + spaces)
        email: Valid email address (validated by EmailStr)
        role: User role (ADMIN, ENTREPRENEUR, PARTNER, etc.)
        is_active: Whether the user account is active (can login)
        is_verified: Whether the user's email is verified
    """
    name: str
    email: EmailStr
    role: UserRole
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserCreate(BaseModel):
    """
    Schema for user registration/creation requests.
    
    Used when:
    - New user registers via POST /api/v1/users
    - Admin creates user via API
    
    Validation rules:
    - name: 2-100 characters, alphanumeric + spaces, hyphens, underscores, @, dots
    - email: Must be valid email format
    - password: 8-128 characters (enforced on server, not transmitted hashed)
    - is_verified: Optional, for admin/testing purposes only
    
    Example:
        >>> data = {
        ...     "name": "John Doe",
        ...     "email": "john@example.com",
        ...     "password": "SecurePass123!"
        ... }
        >>> # POST /api/v1/users with this payload
    
    Note:
        - Passwords are hashed using bcrypt before storage
        - Never return hashed password to client
        - Email verification happens separately
    """
    name: str = Field(..., min_length=2, max_length=100, pattern=r"^[A-Za-z0-9\s\-_@.]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    is_verified: Optional[bool] = None  # Can be set via API for testing/admin


class UserUpdate(BaseModel):
    """
    Schema for user profile update requests.
    
    Used when:
    - User modifies their profile via PATCH /api/v1/users/{id}
    - Admin updates user details
    
    All fields optional - only provided fields are updated.
    
    Attributes:
        name: Updated full name (optional)
        email: Updated email address (optional, triggers reverification)
        password: New password (optional, requires current password verification)
        
    Example:
        >>> data = {
        ...     "name": "Jane Doe",  # Only update name
        ... }
        >>> # PATCH /api/v1/users/user-id with this payload
        
    Note:
        - Use separate endpoint for password changes (includes confirmation)
        - Email changes may require reverification
        - Partial updates supported - omit fields to leave unchanged
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """
    Schema for user information returned from API.
    
    Used in responses from:
    - POST /api/v1/users (after registration)
    - GET /api/v1/users/{id} (retrieve single user)
    - GET /api/v1/users (list users)
    
    Contains all public user information plus timestamps.
    Does NOT include password hash or sensitive fields.
    
    Attributes:
        id: Unique UUID for the user
        name: User's full name
        email: User's email address
        role: User's role (determines permissions)
        is_active: Whether user can login
        is_verified: Whether email is verified
        created_at: Timestamp when user account created
        updated_at: Timestamp of last modification
        
    Example:
        >>> # Response from GET /api/v1/users/123
        >>> {
        ...     "id": "550e8400-e29b-41d4-a716-446655440000",
        ...     "name": "John Doe",
        ...     "email": "john@example.com",
        ...     "role": "ENTREPRENEUR",
        ...     "is_active": true,
        ...     "is_verified": true,
        ...     "created_at": "2024-02-24T10:30:00Z",
        ...     "updated_at": "2024-02-24T15:45:00Z"
        ... }
        
    Note:
        - from_attributes=True allows model reconstruction from ORM objects
        - Timestamps always in UTC
        - Role determines API access and feature availability
    """
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
