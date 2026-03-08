# ADR-004: Dual-Layer Rate Limiting — In-Memory (Dev) + Redis (Production)

**Date:** 2025-10-10  
**Status:** `Accepted`  
**Deciders:** Backend Team

---

## Context

The Bizify API must be protected against abuse, brute-force attacks, and excessive AI usage costs. Rate limiting must:
- Work in single-instance development without Redis
- Scale horizontally in multi-instance production with shared state
- Be configurable without code changes (environment variables)

## Decision Drivers

- **Developer Experience:** Simple local dev without requiring Redis
- **Production Scalability:** Shared counter across multiple API instances
- **Flexibility:** Different limits per endpoint class (auth vs. general API vs. AI)
- **Operational Cost:** Redis is already in the stack for caching — no new service

## Considered Options

| Option | Description |
|--------|-------------|
| **Dual-layer: In-Memory + Redis** | In-memory when `REDIS_ENABLED=false`, Redis when enabled |
| Redis only | Requires Redis in all environments including local dev |
| Nginx rate limiting | Fast but not user-aware; harder to apply per-user logic |
| External service (Cloudflare) | Best for DDoS but not for per-user API rate limiting |

## Decision Outcome

**Chosen option:** Dual-layer middleware — `RateLimiterMiddleware` (in-memory, `sliding_window`) for dev, `RedisRateLimiterMiddleware` for production. Controlled by `REDIS_ENABLED` setting.

### Rate Limit Tiers

| Scope | Default Limit | Window |
|-------|--------------|--------|
| Global API | 100 req | 60 sec |
| Auth endpoints | 10 req | 60 sec |
| AI endpoints | 20 req | 60 sec |

Limits are tracked per `user_id` (authenticated) or per IP (unauthenticated).

### Positive Consequences

- Zero configuration for local development (just set `REDIS_ENABLED=false`)
- Redis sliding window counter prevents burst abuse in production
- `rate_limit_exceeded_total` Prometheus counter tracks violations
- Middleware ordering ensures rate limiting runs before business logic

### Negative Consequences / Trade-offs

- In-memory limiter state is lost on restart (acceptable in dev)
- In-memory limiter is not shared across processes (gunicorn workers each have their own counter)
- Redis dependency becomes a production availability risk (mitigated by health checks)

## Links

- [rate_limiter.py](file:///Users/abdallahabdelrhimantar/Desktop/p7/app/middleware/rate_limiter.py) — In-memory implementation
- [rate_limiter_redis.py](file:///Users/abdallahabdelrhimantar/Desktop/p7/app/middleware/rate_limiter_redis.py) — Redis implementation
- [ADR-003](./003-jwt-rs256-hs256.md) — Auth tokens (JTI blacklist also uses Redis)
- [ADR-005](./005-stripe-event-driven.md) — Stripe billing design
