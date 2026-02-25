# ADR-001: Use FastAPI as the Web Framework

**Date:** 2025-01-08  
**Status:** `Accepted`  
**Deciders:** Backend Team

---

## Context

We need a Python web framework to build the Bizify REST API. The API must support:
- Asynchronous I/O for AI service calls (OpenAI, embeddings)
- Automatic OpenAPI/Swagger documentation generation
- Strong Pydantic-based request/response validation
- High developer velocity for a small team

## Decision Drivers

- **Performance:** Need async-first to handle concurrent AI calls without blocking
- **Developer Experience:** Auto-generated docs reduce manual documentation overhead
- **Type Safety:** Native Pydantic v2 integration enforces schema validation at runtime
- **Ecosystem:** Large community, active development, widely adopted in Python ML/AI projects

## Considered Options

| Option | Description |
|--------|-------------|
| **FastAPI** | Modern async framework, native Pydantic, OpenAPI auto-gen |
| Django REST Framework | Mature, batteries-included, but synchronous by default |
| Flask + extensions | Minimal, flexible, but requires many manual integrations |
| Litestar (formerly Starlite) | FastAPI alternative, slightly less mature ecosystem |

## Decision Outcome

**Chosen option:** FastAPI, because it achieves all decision drivers with minimal configuration.

### Positive Consequences

- Zero-config OpenAPI docs at `/docs` (Swagger) and `/redoc`
- Native `async def` routes enable non-blocking AI and DB calls
- Pydantic v2 schemas serve as both validation and documentation
- `python-jose` + `passlib` integrate cleanly for JWT auth
- Prometheus instrumentation via `prometheus-fastapi-instrumentator`

### Negative Consequences / Trade-offs

- Thinner ORM story than Django (we use SQLAlchemy explicitly)
- Smaller ecosystem than Flask for some edge-case middleware
- Version updates can occasionally break Starlette middleware contracts

## Links

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [ADR-002](./002-postgresql-pgvector.md) — Database choice
- [main.py](file:///Users/abdallahabdelrhimantar/Desktop/p7/main.py) — Application entrypoint
