# Routes Developer Specification

This document describes how routes are implemented and how to add new endpoints consistently.

## Layering Convention

- Route layer: `app/api/routes/...`
- Service layer: `app/services/...`
- Persistence models: `app/models/...`
- API schemas: `app/schemas/...`

Route handlers should stay thin and delegate business rules to services.

## Router Registration

All routers are assembled in `app/api/api.py`.

When adding a new route module:

1. Create route file under the correct domain folder.
2. Import router in `app/api/api.py`.
3. Register via `api_router.include_router(...)`.
4. Add authentication dependency at router-level if required.

## CRUD Endpoint Contract (Preferred)

- `GET /` returns list of schema objects.
- `POST /` accepts create schema, returns created object.
- `GET /{id}` returns one object or `404`.
- `PUT /{id}` accepts update schema, returns updated object.
- `DELETE /{id}` returns deleted object or success marker.

## Validation and Error Handling

- Use Pydantic schemas for request/response.
- Raise `HTTPException` with precise status code and detail.
- Keep service exceptions deterministic and map them at route boundary.
- Enforce ownership/admin checks before data mutation.

## Authentication and Authorization

- Use `Depends(get_current_active_user)` for authenticated endpoints.
- Restrict admin actions explicitly (for example billing plan management).
- Prefer user-scoped queries (`current_user.id`) to prevent data leakage.

## Database Access

- DB sessions are injected through `get_db` from `app/db/database.py`.
- Do not keep long-lived sessions in global scope.
- Use transactions for multi-step writes.

## Naming

- Route files: singular resource topic (example: `idea_metric.py`).
- Service files: `<resource>_service.py` or focused modules for subdomains.
- Schema/model classes: singular and descriptive (`IdeaMetricCreate`, `IdeaMetricOut`).

## Testing Requirements

For each new route:

1. Add API tests in `tests/api/...`.
2. Add unit tests for new service logic in `tests/unit/...`.
3. Add integration tests when workflow spans multiple services.
4. Add security tests for permission boundaries if route is sensitive.

## Example Skeleton

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.example import ExampleCreate, ExampleOut
from app.services.example.example_service import create_example

router = APIRouter()

@router.post("/", response_model=ExampleOut)
def create_item(
    payload: ExampleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    try:
        return create_example(db, payload, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```
