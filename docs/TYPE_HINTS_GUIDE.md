# Type Hints Documentation & Implementation Guide

## Overview

Type hints are optional annotations in Python that specify expected data types. They improve code quality, enable IDE autocomplete, catch type errors early, and make code self-documenting.

**Current Status:** 56% coverage
**Target:** 90% coverage
**Benefit:** Production-ready IDE support, fewer runtime type errors

---

## 1. Type Hints Fundamentals

### Basic Syntax

```python
# Function arguments and return types
def get_user(user_id: int) -> User:
    """user_id is int, returns User object"""
    return db.query(User).filter(User.id == user_id).first()

# Variable type hints
user_count: int = 0
email: str = "user@example.com"
is_active: bool = True

# Optional values (can be None)
from typing import Optional
def find_user(user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

# Collections
from typing import List, Dict, Set, Tuple
def get_all_users() -> List[User]:
    return db.query(User).all()

def user_stats() -> Dict[str, int]:
    return {"total": 100, "active": 85}

# Union types (multiple possible types)
from typing import Union
def process_payload(data: Union[str, dict]) -> None:
    if isinstance(data, str):
        print(f"String: {data}")
    else:
        print(f"Dict: {data}")
```

### Benefits

| Benefit | Example |
|---------|---------|
| **IDE Autocomplete** | Type `user.` and see all available methods |
| **Early Error Detection** | MyPy catches type mismatches before runtime |
| **Self-Documenting** | Code shows expected types without reading docs |
| **Refactoring Safety** | Changing types breaks code compilation, not runtime |
| **Reduced Bugs** | ~15% fewer runtime errors in typed projects |

---

## 2. SQLAlchemy Type Hints (New Style)

### SQLAlchemy 2.0+ with Python 3.9+

New modern approach using `Mapped`:

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    # Using mapped_column and Mapped
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships with proper type hints
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Optional relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id"))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")
```

### Benefits of Mapped[]

```python
# Without type hints - no autocomplete
subscription = db.query(Subscription).first()
subscription.user.  # IDE doesn't know what methods are available

# With Mapped[] - full IDE support
subscription: Mapped["Subscription"] = db.query(Subscription).first()
subscription.user.  # IDE shows: email, username, created_at, subscriptions...
```

---

## 3. Service Layer Type Hints

### Before (Minimal Types)

```python
def get_user(db, user_id):
    """Get user by ID - what types are these?"""
    user = db.query(User).filter(User.id == user_id).first()
    return user

def update_user(db, user_id, data):
    """Returns what? Updates what fields?"""
    user = db.query(User).get(user_id)
    if user:
        for key, value in data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

def get_all_users(db, skip=0, limit=100):
    """Returns what type of list?"""
    return db.query(User).offset(skip).limit(limit).all()
```

### After (Full Type Hints)

```python
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """
    Fetch user by ID.
    
    Args:
        db: Database session
        user_id: UUID of user to fetch
    
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()

def update_user(
    db: Session,
    user_id: UUID,
    data: Dict[str, Any]
) -> Optional[User]:
    """
    Update user fields.
    
    Args:
        db: Database session
        user_id: UUID of user to update
        data: Dictionary of fields to update
    
    Returns:
        Updated User object if found, None otherwise
    
    Raises:
        ValidationError: If data contains invalid fields
    """
    user: Optional[User] = db.query(User).filter(
        User.id == user_id
    ).first()
    
    if user is None:
        return None
    
    # Validate fields before update
    allowed_fields = {"username", "email", "bio", "avatar_url"}
    invalid_fields = set(data.keys()) - allowed_fields
    
    if invalid_fields:
        raise ValidationError(
            message=f"Cannot update fields: {invalid_fields}",
            field="data",
            details={"invalid_fields": list(invalid_fields)}
        )
    
    for key, value in data.items():
        if value is not None:  # Don't update None values
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

def get_users_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[User]:
    """
    Fetch multiple users with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 100)
    
    Returns:
        List of User objects
    
    Raises:
        ValidationError: If pagination params are invalid
    """
    if skip < 0:
        raise ValidationError(
            message="skip must be >= 0",
            field="skip",
            details={"received": skip}
        )
    
    if limit < 1 or limit > 1000:
        raise ValidationError(
            message="limit must be between 1 and 1000",
            field="limit",
            details={"received": limit, "min": 1, "max": 1000}
        )
    
    return db.query(User).offset(skip).limit(limit).all()
```

---

## 4. Complex Type Hints Patterns

### Union Types (Multiple Possible Types)

```python
from typing import Union, Literal

# Strict union
def process_result(result: Union[str, int, float]) -> None:
    """Can accept string, int, or float"""
    if isinstance(result, str):
        print(f"String result: {result}")
    elif isinstance(result, int):
        print(f"Int result: {result}")
    else:
        print(f"Float result: {result}")

# Using Literal for specific string values
def set_status(status: Literal["active", "inactive", "pending"]) -> None:
    """Only accepts these specific string values"""
    # If you write set_status("invalid"), MyPy will error
    pass

set_status("active")  # ✅ OK
set_status("invalid")  # ❌ MyPy error: Not a literal of ("active", "inactive", "pending")
```

### Generic Types

```python
from typing import Generic, TypeVar

T = TypeVar('T')  # Generic type variable

class Repository(Generic[T]):
    """Generic repository that works with any model type"""
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Returns instance of T or None"""
        pass
    
    def get_all(self) -> List[T]:
        """Returns list of T"""
        pass
    
    def create(self, obj: T) -> T:
        """Creates and returns instance of T"""
        pass

# Usage
user_repo = Repository[User]()
users: List[User] = user_repo.get_all()  # IDE knows it's List[User]

subscription_repo = Repository[Subscription]()
sub: Optional[Subscription] = subscription_repo.get_by_id(123)
```

### Callable Types

```python
from typing import Callable

# Function that accepts a callback
def process_with_callback(
    data: List[int],
    callback: Callable[[int], str]  # Takes int, returns str
) -> List[str]:
    """Apply callback to each item in data"""
    return [callback(item) for item in data]

# Usage
def format_number(n: int) -> str:
    return f"Number: {n}"

results = process_with_callback([1, 2, 3], format_number)
# results is List[str]
```

---

## 5. API Routes Type Hints

### Before

```python
@router.post("/users")
def create_user(data: UserCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Create new user - unsafe types"""
    user = crud.create_user(db, data)
    return user
```

### After

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Create a new user.
    
    Args:
        data: User creation data (validated by Pydantic)
        db: Database session
        current_user: Authenticated user (admin only)
    
    Returns:
        Created user as UserResponse
    
    Raises:
        ValidationError: Invalid input data
        AccessDeniedError: User not admin
    """
    # Check admin
    if not current_user.is_admin:
        raise AccessDeniedError(
            action="create",
            resource_type="user"
        )
    
    # Create user
    user: User = crud.create_user(db, data)
    return UserResponse.from_orm(user)

@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get user by ID"""
    user: Optional[User] = crud.get_user(db, user_id)
    
    if not user:
        raise ResourceNotFoundError(
            resource_type="User",
            resource_id=str(user_id)
        )
    
    # Authorization check
    if user.id != current_user.id and not current_user.is_admin:
        raise AccessDeniedError(
            action="read",
            resource_type="user"
        )
    
    return UserResponse.from_orm(user)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Update user"""
    user: Optional[User] = crud.get_user(db, user_id)
    
    if not user:
        raise ResourceNotFoundError(
            resource_type="User",
            resource_id=str(user_id)
        )
    
    if user.id != current_user.id and not current_user.is_admin:
        raise AccessDeniedError(
            action="update",
            resource_type="user"
        )
    
    updated: User = crud.update_user(db, user_id, data)
    return UserResponse.from_orm(updated)

@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete user"""
    user: Optional[User] = crud.get_user(db, user_id)
    
    if not user:
        raise ResourceNotFoundError(
            resource_type="User",
            resource_id=str(user_id)
        )
    
    if user.id != current_user.id and not current_user.is_admin:
        raise AccessDeniedError(
            action="delete",
            resource_type="user"
        )
    
    crud.delete_user(db, user_id)
```

---

## 6. MyPy Configuration

### Current Configuration (`mypy.ini`)

```ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_optional = True
no_implicit_optional = True

# SQLAlchemy plugin for better ORM support
plugins = sqlalchemy.ext.mypy.plugin

# Ignore third-party libraries without types
ignore_missing_imports = True

[mypy-tests.*]
# Tests can be less strict
ignore_errors = True

[mypy-alembic.*]
ignore_errors = True
```

### Running MyPy

```bash
# Check entire project
mypy app/

# Check specific file
mypy app/services/billing/payment_service.py

# Strict mode (most strict checking)
mypy app/ --strict

# Show all errors
mypy app/ --show-error-codes

# Check with SQLAlchemy plugin
mypy app/ --plugins sqlalchemy.ext.mypy.plugin
```

---

## 7. Implementation Priority

### Tier 1: Critical (High Impact, Easy)

**Files to update:** 15-20 files
**Effort:** 4-6 hours

#### Models with Relationships

Files in `app/models/`:
```
- users/user.py              # User, UserProfile, RefreshToken
- billing/subscription.py    # Subscription with Plan/User relationships
- billing/payment.py         # Payment with Subscription relationship
- chat/conversation.py       # Conversation with User/Messages
- ideation/idea.py          # Idea with User/Comments
- business/business.py       # Business with User/Departments
```

Example transformation:

**Before:**
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True)
    subscriptions = relationship("Subscription", back_populates="user")
```

**After:**
```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from uuid import UUID

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="user"
    )
```

### Tier 2: Important (Medium Impact, Medium Effort)

**Files to update:** 20-30 files
**Effort:** 6-8 hours

#### Service Layer Functions

Files in `app/services/`:
- billing/payment_service.py
- billing/subscription_service.py
- billing/plan_service.py
- chat/conversation_service.py
- ideation/idea_service.py
- business/business_service.py
- users/user_service.py
- ...others

Add return types and parameter types to all functions.

### Tier 3: Nice-to-Have (Lower Priority)

**Files to update:** 40+ files
**Effort:** 8-10 hours

#### Helper Functions & Utils
- crud_utils.py
- pagination.py
- decorators
- middleware functions

---

## 8. Common Type Hints Patterns

### Optional vs Union[..., None]

```python
# These are equivalent:
def get_user(id: int) -> Optional[User]:
    pass

def get_user(id: int) -> Union[User, None]:
    pass

# But Optional is clearer
# Use Optional when something can be None
```

### List vs Sequence

```python
from typing import List, Sequence

# Use List when you can modify it
def add_user(users: List[User]) -> None:
    users.append(new_user)  # OK

# Use Sequence when read-only
def print_users(users: Sequence[User]) -> None:
    for user in users:
        print(user)  # OK
    users.append(new_user)  # ❌ Error: can't append to Sequence
```

### Dict vs Mapping

```python
from typing import Dict, Mapping

# Use Dict when you can modify it
def update_config(config: Dict[str, str]) -> None:
    config["new_key"] = "value"  # OK

# Use Mapping when read-only
def log_config(config: Mapping[str, str]) -> None:
    for key, value in config.items():
        print(f"{key}={value}")  # OK
    config["new_key"] = "value"  # ❌ Error
```

---

## 9. Validation Against Type Hints

```python
from typing import Optional
from uuid import UUID

def create_subscription(
    db: Session,
    user_id: UUID,
    plan_id: UUID
) -> Subscription:
    """
    Type hints serve as implicit validation.
    """
    # If someone passes string instead of UUID:
    subscription = create_subscription(
        db=session,
        user_id="not-a-uuid",  # ❌ MyPy error
        plan_id=valid_uuid
    )
    
    # MyPy will catch this before runtime!
```

### MyPy Output

```
app/api/routes.py:45: error: Argument "user_id" to "create_subscription" has 
  incompatible type "str"; expected "UUID"
Found 1 error in 1 file (checked 120 source files)
```

---

## 10. Type Hints for Error Handling

```python
from typing import Optional, Callable, Any
from app.core.exceptions import AppException, ValidationError

def validate_and_process(
    data: Dict[str, Any],
    validator: Callable[[Dict[str, Any]], bool],
    processor: Callable[[Dict[str, Any]], Any]
) -> Optional[Any]:
    """
    Type hints show what validator and processor should do.
    
    Args:
        data: Input dictionary
        validator: Function that takes dict, returns bool
        processor: Function that takes dict, returns Any result
    
    Returns:
        Result of processor or None if validation fails
    
    Raises:
        ValidationError: If validator returns False
    """
    try:
        if not validator(data):
            raise ValidationError(
                message="Validation failed",
                field="data",
                details=data
            )
        
        return processor(data)
    
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(
            message=str(e),
            field="data",
            details={"error": str(e)}
        )
```

---

## 11. Testing with Type Hints

```python
import pytest
from typing import Optional, List
from uuid import UUID

def test_get_user_returns_user_or_none() -> None:
    """Test function also has type hints."""
    user_id: UUID = UUID("123e4567-e89b-12d3-a456-426614174000")
    
    result: Optional[User] = user_service.get_user(db, user_id)
    
    # result is properly typed for assertions
    if result is not None:
        assert isinstance(result, User)
        assert result.id == user_id

def test_get_all_users_returns_list() -> None:
    """Get all users returns List[User]."""
    users: List[User] = user_service.get_all_users(db)
    
    assert isinstance(users, list)
    for user in users:
        assert isinstance(user, User)
```

---

## 12. Migration Checklist

- [ ] Enable strict mode in mypy.ini
- [ ] Add type hints to all model files (Tier 1)
- [ ] Add return types to all service functions (Tier 1-2)
- [ ] Add parameter types to all service functions (Tier 1-2)
- [ ] Add type hints to route handlers (Tier 2)
- [ ] Add type hints to helper utilities (Tier 3)
- [ ] Run `mypy app/ --strict` and fix all errors
- [ ] Run tests: `pytest tests/ --cov=app`
- [ ] Document type hints strategy in project README

---

## 13. IDE Integration

### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
    "python.linting.mypyEnabled": true,
    "python.linting.mypyArgs": [
        "--strict",
        "--no-implicit-optional",
        "--warn-redundant-casts"
    ],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "ms-python.python"
    }
}
```

### Benefits

- ✅ Real-time type checking as you code
- ✅ Autocomplete suggestions
- ✅ Quick info on hover
- ✅ Inline error messages
- ✅ Code refactoring with type safety

---

## 14. Further Reading

### Official Documentation
- [Python typing module](https://docs.python.org/3/library/typing.html)
- [SQLAlchemy 2.0 Type Hints](https://docs.sqlalchemy.org/en/20/orm/declare_api.html)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)

### Best Practices
- Always hint function return types
- Always hint function parameter types
- Use `Optional[T]` instead of `Union[T, None]`
- Use `Literal[]` for specific string/enum values
- Use `Mapping` for read-only dicts
- Use `Sequence` for read-only lists

---

## Quick Start

### Step 1: Update Models
```bash
# Start with billings models (most critical relationships)
cd app/models/billing/
# Edit: subscription.py, payment.py, plan.py
```

### Step 2: Check Types
```bash
mypy app/models/ --strict
```

### Step 3: Update Services
```bash
# Add return and parameter types
cd app/services/billing/
# Edit: payment_service.py, subscription_service.py
```

### Step 4: Update Routes
```bash
cd app/api/routes/
# Add types to route handlers
```

### Step 5: Verify
```bash
mypy app/ --strict
pytest tests/
```

---

## Expected Impact

After implementing full type hints (90% coverage):

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Type Coverage** | 56% | 90% | +34% |
| **IDE Autocomplete** | Limited | Full | 100% |
| **Type Errors Caught Early** | None | Most | ↑↑↑ |
| **Development Speed** | Slower | Faster | +20% |
| **Runtime Type Crashes** | Occasional | Rare | -70% |
| **Code Maintainability** | 76% | 85% | +9% |

---

## Summary

Type hints are:
- ✅ Optional (Python still runs without them)
- ✅ Powerful (when used with MyPy)
- ✅ Self-documenting (types show intent)
- ✅ IDE-enhancing (enables autocomplete)
- ✅ Worth the effort (catches bugs early)

**Start with Tier 1 files** (models) for maximum impact with minimum effort.
