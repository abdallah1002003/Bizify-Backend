# Backend & AI Service — Fix Log

> **For teammates:** Every change made to the backend (`Bizify-Backend`) and AI service (`bizifyAI`) is recorded here in chronological order.
> Each entry has: what broke, what file was changed, what the fix does, and why it matters.
> Updated automatically whenever the project is edited.

---

## Table of Contents

1. [AI ↔ Backend Integration Fixes](#1-ai--backend-integration-fixes)
2. [Frontend-Readiness Fixes](#2-frontend-readiness-fixes)
3. [Security Audit Fixes — Critical](#3-security-audit-fixes--critical)
4. [Security Audit Fixes — High](#4-security-audit-fixes--high)
5. [Remaining Issues Resolved](#5-remaining-issues-resolved)
6. [Files Changed — Quick Reference](#6-files-changed--quick-reference)

---

## 1. AI ↔ Backend Integration Fixes

These fixes were found during an audit of how the backend proxies calls to the AI service.

---

### Fix 1.1 — `skills_json` crash on profile analysis

**File:** `bizifyAI/db/crud.py` → `get_skills_from_profile()` (line ~113)

**Problem:**
The backend stores skills in `user_profiles.skills_json` as a list of dicts:
```json
[{ "id": "abc", "name": "Python", "rating": 3 }]
```
But the AI's `run_profile_analysis()` called `s.lower()` on each item — which crashes with `AttributeError: 'dict' object has no attribute 'lower'` when the user has any skills saved.

**Fix:**
`get_skills_from_profile()` now extracts the `"name"` field from each dict before returning, so the AI always receives `["Python", "JavaScript"]` instead of raw dicts.

```python
# Before
return skills  # list of dicts — crashes downstream

# After
return [s["name"] if isinstance(s, dict) else s for s in skills]
```

---

### Fix 1.2 — Idea intake "not ready" guard never triggered

**File:** `bizifyAI/routes/idea_intake.py` (lines 26, 47)

**Problem:**
Both guards that prevent starting problem discovery before the idea intake is complete checked:
```python
if not intake or intake.get("_status") == "pending_clarification":
```
But the `IdeaIntakeResult.data` property returns `decision`, not `_status`. The guard was effectively dead code — `_status` always returned `None`, so the check never blocked anything.

**Fix:**
```python
# Before
if not intake or intake.get("_status") == "pending_clarification":

# After
if not intake or intake.get("decision") == "needs_clarification":
```

---

### Fix 1.3 — `user_id` not injected on 30 backend AI endpoints (security)

**File:** `Bizify-Backend/app/api/v1/ai_pipeline.py`

**Problem:**
30 POST endpoints forwarded raw frontend payloads to the AI service without overwriting `user_id`. Any authenticated user could send another user's `user_id` in the body and read or modify their startup data.

**Affected endpoints (before fix):**
`/idea-intake`, `/idea-intake/start-chat`, `/explain`, and every `/chat`, `/chat/stream`, and `/regenerate-custom` for all 9 analysis sections.

**Fix:**
Every affected endpoint now sets `payload["user_id"] = str(current_user.id)` before forwarding. The backend's JWT determines which user is acted on — the frontend cannot influence this.

---

### Fix 1.4 — AI service URL hardcoded to production

**File:** `Bizify-Backend/app/services/ai_pipeline_service.py` (line 15)

**Problem:**
```python
_AI_PIPELINE_URL = "https://bizifyai-production.up.railway.app/pipeline/run"
```
Hardcoded production URL. Staging and dev environments always hit production, making testing impossible without the real AI service.

**Fix:**
```python
_AI_PIPELINE_URL = f"{settings.AI_PIPELINE_BASE_URL}/pipeline/run"
```
Now reads from `settings.AI_PIPELINE_BASE_URL` which is set per environment in `.env`.

---

### Fix 1.5 — Duplicated ternary in URL builder

**File:** `Bizify-Backend/app/api/v1/ai_pipeline.py` → `_forward_post_to_ai()`

**Problem:**
```python
target_url = f"{url}/{path}/{user_id}" if user_id else f"{url}/{path}" if user_id else f"{url}/{path}"
```
The second `if user_id` is always `False` at that point — the third branch is always unreachable. Confusing and wrong-looking.

**Fix:**
```python
target_url = f"{url}/pipeline/{path}/{user_id}" if user_id else f"{url}/pipeline/{path}"
```

---

## 2. Frontend-Readiness Fixes

Fixes found during a full API audit in preparation for frontend integration.

---

### Fix 2.1 — Health/version-check behind subscription gate

**Files:** `Bizify-Backend/app/api/v1/ai_pipeline.py`, `Bizify-Backend/app/api/api.py`

**Problem:**
`GET /api/v1/ai/health` and `GET /api/v1/ai/version-check` were registered on the same router as all AI endpoints, which had `dependencies=[Depends(check_ai_usage)]` at the router level. This meant:
- No subscription → `403 Forbidden` even for a health check
- The frontend could not check if the AI service was alive without a paid plan

**Fix:**
Created a separate `_system_router = APIRouter()` (no dependencies) and moved both endpoints there. Registered `_system_router` alongside the main router in `api.py`.

---

### Fix 2.2 — No global exception handler

**File:** `Bizify-Backend/app/main.py`

**Problem:**
Unhandled exceptions (DB errors, unexpected crashes) returned an unformatted Starlette 500 response with internal stack-trace details — not a consistent `{"detail": "..."}` JSON the frontend could safely handle.

**Fix:**
Added two exception handlers:
```python
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(...):
    return JSONResponse(500, {"detail": "A database error occurred."})

@app.exception_handler(Exception)
async def unhandled_exception_handler(...):
    return JSONResponse(500, {"detail": "An unexpected error occurred."})
```

---

### Fix 2.3 — AI GET endpoint response_model annotations were wrong

**File:** `Bizify-Backend/app/api/v1/ai_pipeline.py`

**Problem:**
Schema definitions like `AICustomersResponse(customers: list[dict])` did not match what the AI actually returns (`customers: dict`). FastAPI's response validation would either silently coerce the data or raise a 500 error.

**Fix:**
Removed all incorrect `response_model=` annotations from the 11 GET AI endpoints. They now return the raw dict from the AI service, which is what the frontend expects.

---

### Fix 2.4 — Created frontend handoff document

**File:** `Bizify-Backend/handoff_to_frontend.md` (new, 2100+ lines)

Complete integration guide for the frontend AI agent covering:
- All 70+ API endpoints with exact request/response shapes
- TypeScript interfaces for every model
- Full auth flow and token rules
- AI pipeline flows (new user and returning user)
- SSE streaming implementation
- 13 critical warnings about gotchas

---

## 3. Security Audit Fixes — Critical

Found during a full read of every service, repository, and route file.

---

### Fix 3.1 — OTP leaked in HTTP response body

**File:** `Bizify-Backend/app/services/user_service.py` → `create_otp()` (line ~143)

**Severity:** CRITICAL

**Problem:**
When SMTP delivery fails, the raw OTP code was returned in the API `detail` field:
```python
raise HTTPException(
    detail=f"Could not send email. Verification code: {otp}",  # ← OTP IN PLAIN TEXT
)
```
An attacker could register, disable SMTP (or use a provider that rejects delivery), read the OTP from the 503 response, and verify the account without email access.

**Fix:**
```python
# Before
detail=f"Could not send email. Verification code: {otp}"

# After
detail="Could not send verification email. Please try again later."
```
The OTP is now only logged server-side (never returned to clients).

---

### Fix 3.2 — Password reset does NOT invalidate existing tokens

**File:** `Bizify-Backend/app/services/user_service.py` → `reset_password_logic()` (line ~200)

**Severity:** CRITICAL

**Problem:**
`get_current_user` in `dependencies.py` checks `issued_at < user.last_password_change` to invalidate old tokens after a password reset. But `last_password_change` was never set during password reset — so the field was always `None`, the check never triggered, and attacker tokens stayed valid forever even after the victim reset their password.

**Fix:**
```python
user.password_hash = get_password_hash(new_password)
user.last_password_change = datetime.now(timezone.utc)  # ← ADDED
```

---

### Fix 3.3 — Paymob subscription activated before payment confirmed

**File:** `Bizify-Backend/app/services/payment_service.py` → `create_paymob_payment()` (line ~213)

**Severity:** CRITICAL

**Problem:**
When initiating a Paymob (Visa/Mastercard) checkout:
```python
# subscription immediately set to ACTIVE
subscription = subscription_repo.create_or_update(db, user_id=user_id, ...)
# payment only pending
payment = payment_repo.create_paymob_payment(..., status="pending")
```
Users got full AI access as soon as they clicked "Pay with card" — even if they closed the browser, the card was declined, or the payment never completed.

**Fix:**
Subscription is now created with `status=PENDING`. The Paymob webhook (which already existed and fires on confirmed payment) sets it to `ACTIVE`. Users can only access AI features after confirmed payment.

---

### Fix 3.4 — PayPal `plan_id` not verified against captured amount

**File:** `Bizify-Backend/app/services/payment_service.py` → `capture_payment()` (line ~92)

**Severity:** CRITICAL

**Problem:**
The capture endpoint accepted `{ order_id, plan_id }` from the frontend. An attacker could:
1. Create a PayPal order for the cheapest plan ($5)
2. Get user approval
3. Send the capture request with a premium `plan_id` ($50/mo)
→ Get premium subscription for $5.

**Fix:**
After capturing from PayPal, the captured amount is checked against the plan's actual price:
```python
if captured_amount < Decimal(str(plan.price)):
    raise HTTPException(402, "Captured amount does not match the plan price.")
```

---

### Fix 3.5 — `test-email` endpoint was public and unauthenticated

**File:** `Bizify-Backend/app/api/v1/auth.py` → `test_email()` (line ~123)

**Severity:** HIGH

**Problem:**
`GET /api/v1/auth/test-email?email=anyone@example.com` sent a real email from the backend's SMTP server to any address with no auth required — a spam relay.

**Fix:**
- Requires `Authorization: Bearer <token>`
- Rejects non-ADMIN roles with 403
- Hidden from Swagger (`include_in_schema=False`)

---

## 4. Security Audit Fixes — High

---

### Fix 4.1 — Token blacklist grows without bound

**File:** `Bizify-Backend/app/repositories/auth_repo.py` → `is_token_blacklisted()`

**Problem:**
Every logout inserted a row into `token_blacklist`. There was no expiry, no TTL, no cleanup. After millions of logouts, the `is_token_blacklisted()` call (which runs on **every single authenticated request**) would do a full table scan, progressively slowing down every API call.

**Fix:**
- Added `_BLACKLIST_TTL_DAYS = 8` constant (tokens expire in 7 days; 8-day window is safe)
- `is_token_blacklisted()` now filters: `blacklisted_at >= now - 8 days` — expired entries are never matched, even without cleanup
- Added `purge_expired()` helper to delete old entries (call from a scheduled job or startup)

---

### Fix 4.2 — `last_activity` None edge case in session timeout

**File:** `Bizify-Backend/app/api/dependencies.py` → `get_current_user()` (line ~96)

**Problem:**
```python
if last_activity and last_activity.tzinfo is None:
    last_activity = last_activity.replace(tzinfo=timezone.utc)
else:
    last_activity = last_activity or now  # ← fires when last_activity is None
```
When `last_activity` is `None` (new user, or race condition), it defaults to `now`, meaning the inactivity timeout is never triggered on the first request with that token. Minor edge case since the model has a default, but a logic bug.

**Fix:**
```python
if last_activity is None:
    last_activity = now          # treat as just-active, no timeout
elif last_activity.tzinfo is None:
    last_activity = last_activity.replace(tzinfo=timezone.utc)
```

---

## 5. Remaining Issues Resolved

---

### Fix 5.1 — Rate limiting on public auth endpoints

**Files:** `Bizify-Backend/requirements.txt`, `Bizify-Backend/app/core/limiter.py` (new), `Bizify-Backend/app/main.py`, `Bizify-Backend/app/api/v1/auth.py`

**Problem:**
`POST /auth/forgot-password` and `POST /auth/resend-verification-otp` had no rate limiting per IP. An attacker could hammer them to enumerate users (timing differences), trigger unlimited emails, or probe OTP validity.

**Fix:**
Added `slowapi` (FastAPI rate-limiter):
- New file `app/core/limiter.py` with shared `Limiter` instance
- Limiter registered on the FastAPI app in `main.py`
- Limits applied per IP:

| Endpoint | Limit |
|----------|-------|
| `POST /auth/login` | 10/minute |
| `POST /auth/google/callback` | 10/minute |
| `POST /auth/verify-otp` | 10/minute |
| `POST /auth/resend-verification-otp` | 3/minute |
| `POST /auth/forgot-password` | 3/minute |
| `POST /auth/verify-reset-code` | 10/minute |
| `POST /auth/reset-password` | 5/minute |

Returns `429 Too Many Requests` when limit is exceeded.

---

### Fix 5.2 — `get_all_users()` hardcoded limit of 1000 rows

**File:** `Bizify-Backend/app/services/user_service.py` → `get_all_users()`

**Problem:**
```python
def get_all_users(db): return user_repo.get_multi(db, skip=0, limit=1000)
```
No pagination. Would load 1000 user rows into memory on every call.

**Fix:**
```python
def get_all_users(db, skip=0, limit=100):
    return user_repo.get_multi(db, skip=skip, limit=min(limit, 500))
```
Max 500 rows per call, with proper `skip`/`limit` pagination. Note: the admin route in `admin.py` already used `user_repo.get_multi` directly with its own pagination — this fixes the service method for any code that calls it.

---

### Fix 5.3 — No DB index on `token_blacklist.blacklisted_at`

**File:** `Bizify-Backend/alembic/versions/a1b2c3d4e5f6_add_token_blacklist_index.py` (new migration)

**Problem:**
Fix 4.1 added a TTL filter on `blacklisted_at`. Without an index, this filter scans the entire table on every authentication request.

**Fix:**
New Alembic migration creates `ix_token_blacklist_blacklisted_at`:
```sql
CREATE INDEX ix_token_blacklist_blacklisted_at ON token_blacklist (blacklisted_at);
```

**Action required:** Run `alembic upgrade head` to apply.

---

### Fix 5.4 — AI service CORS allowed all browser origins (`"*"`)

**Files:** `bizifyAI/agents/config.py`, `bizifyAI/main.py`

**Problem:**
```python
allow_origins=["*"]  # any browser could call the AI service directly
```
The AI service is supposed to be called only by the backend server — never by browsers. The wildcard allowed anyone who knew the URL to call it directly, bypassing the backend's auth and subscription checks (though the `X-API-KEY` header is still required).

**Fix:**
- Added `ALLOWED_ORIGINS` environment variable to `agents/config.py`
- AI service CORS now reads from that variable; defaults to `[]` (blocks all browser origins)
- Set `ALLOWED_ORIGINS=https://your-backend-host` in the AI service `.env` for production
- Restricted `allow_methods` to `["POST", "GET"]` and `allow_headers` to `["x-api-key", "Content-Type"]`

---

### Fix 5.5 — Usage counter consumed even when AI call fails

**Files:** `Bizify-Backend/app/api/dependencies.py`, `Bizify-Backend/app/api/v1/ai_pipeline.py`

**Problem:**
`check_ai_usage` (a FastAPI dependency that runs before the route handler) called `usage_repo.increment()` before the AI request was made. If the AI service was down, returned an error, or timed out, the user still lost one of their monthly AI requests.

Additionally, GET requests (reading previously generated data) consumed quota even though they are read-only.

**Fix:**
- Removed `usage_repo.increment()` from `check_ai_usage`
- Moved it into `_forward_post_to_ai()`, called only **after** `response.raise_for_status()` confirms success
- GET requests (`_forward_get_to_ai`) never increment — reading your own data is free
- Failed AI calls (any error) never consume quota
- The increment failure is non-fatal: a DB error during increment won't break the AI response

---

## 6. Files Changed — Quick Reference

### `Bizify-Backend` (backend)

| File | Changes |
|------|---------|
| `app/api/v1/auth.py` | Rate limiting on all auth endpoints; `test-email` locked to ADMIN |
| `app/api/v1/ai_pipeline.py` | Fixed 30 missing `user_id` injections; removed wrong `response_model` annotations; health/version to `_system_router`; usage increment moved here (POST success only); fixed duplicated ternary |
| `app/api/api.py` | Registered `_system_router` for health/version endpoints |
| `app/api/dependencies.py` | Fixed `last_activity` None edge case; removed usage increment (moved to forwarding helper) |
| `app/services/auth_service.py` | — (no changes; audited clean) |
| `app/services/user_service.py` | Fixed OTP leak in HTTP response; added `last_password_change` on password reset; fixed `get_all_users` limit |
| `app/services/payment_service.py` | Fixed Paymob subscription PENDING until webhook; added PayPal amount verification; added missing imports |
| `app/services/ai_pipeline_service.py` | Fixed hardcoded production URL |
| `app/repositories/auth_repo.py` | Added TTL filter to blacklist check; added `purge_expired()` |
| `app/core/limiter.py` | **NEW** — shared slowapi rate-limiter instance |
| `app/main.py` | Registered rate limiter + 429 handler; added global SQLAlchemy + Exception handlers |
| `requirements.txt` | Added `slowapi` |
| `alembic/versions/a1b2c3d4e5f6_add_token_blacklist_index.py` | **NEW** — index on `token_blacklist.blacklisted_at` |
| `handoff_to_frontend.md` | **NEW** — complete 2100-line frontend integration guide |

### `bizifyAI` (AI service)

| File | Changes |
|------|---------|
| `agents/config.py` | Added `ALLOWED_ORIGINS` env variable |
| `main.py` | Fixed CORS from `"*"` to env-controlled list; restricted allowed methods/headers |
| `db/crud.py` | Fixed `get_skills_from_profile()` — extracts `name` from skill dicts |
| `routes/idea_intake.py` | Fixed both `_status` guards to use `decision == "needs_clarification"` |

---

---

## Post-2026-05-18 Fixes (detected during 2026-05-19 full audit)

---

### Fix 6.1 — `SubscriptionStatus.PENDING` missing from enum (crash on Paymob payment)

**File:** `Bizify-Backend/app/models/subscription.py`, new migration `b2c3d4e5f6a1_add_pending_subscription_status.py`

**Severity:** CRITICAL

**Problem:**
Fix 3.3 added `status=SubscriptionStatus.PENDING` to the Paymob payment flow, but `PENDING` was never added to the `SubscriptionStatus` enum. The enum only had `ACTIVE` and `CANCELED`. Every Paymob checkout attempt would raise `AttributeError: 'PENDING' is not a valid SubscriptionStatus` at runtime.

**Fix:**
- Added `PENDING = "PENDING"` to `SubscriptionStatus` in `app/models/subscription.py`
- New Alembic migration `b2c3d4e5f6a1` adds the value to the PostgreSQL enum type: `ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'PENDING'`

**Action required:** Run `alembic upgrade head`.

---

### Fix 6.2 — Syntax errors in three AI agent files (already self-healed)

**Files:** `bizifyAI/agents/EightBusinessModel.py`, `bizifyAI/agents/ElevenUnitEconomicsAgent.py`, `bizifyAI/agents/SixMaketPotential.py`

**Problem detected, then found already fixed:**
A syntax check at the start of the audit found "expected 'except' or 'finally' block" in all three files. On reading the files, they were already corrected — the `chat_*` functions had been moved to module level and the `try/except` blocks properly closed. The errors existed in an intermediate state during a refactor and were self-corrected before this audit ran a second check.

**Current state:** All three files pass syntax check. No action needed.

---

### New features detected (AI service) — documentation only

These features were added by the team and are already working. No fixes needed.

| Feature | Files | What it does |
|---------|-------|-------------|
| **Tavily search integration** | `agents/config.py`, `agents/search_pipeline.py`, all agent files | Replaces Serper+BS4 with Tavily API for richer, pre-cleaned search results. Falls back to Serper if `TAVILY_API_KEY` is not set. Add `TAVILY_API_KEY=tvly-...` to AI service `.env`. |
| **Groq extraction model** | `agents/config.py` | `GROQ_EXTRACTION_MODEL = "llama-3.1-8b-instant"` — fast/cheap model used only for structured JSON extraction from search results; main analysis still uses `GROQ_MODEL`. |
| **`tokens_used` in responses** | `routes/dependencies.py` (SSE `done` event), `routes/pipeline.py` (`/pipeline/chat`) | Every streaming `done` event now includes `"tokens_used": <number>`. Non-streaming `/pipeline/chat` includes it at the top level. |
| **Real questionnaire in idea-intake start-chat** | `routes/idea_intake.py`, `orchestrator/orchestrator.py`, `agents/ThreeIdeaIntakeAgent.py` | `_build_questionnaire_for_problem_discovery` now accepts an optional `real_questionnaire` dict. Returning users who completed onboarding get their real founder profile injected into problem discovery instead of hardcoded defaults. |
| **Usage increment for general-chat and streams** | `Bizify-Backend/app/api/v1/ai_pipeline.py` | `general_chat` and `general_chat_stream` now increment the usage counter after a successful response. Streaming routes increment on first chunk. |

---

### Noted (design, not bugs)

| Item | Status |
|------|--------|
| Users with NO subscription get 100 free AI requests (freemium) | Intentional — `AI_REQUEST_DEFAULT_LIMIT = 100` in `usage_repo.py` |
| `stream_options={"include_usage": True}` in SSE helper | Groq may silently ignore unsupported params; code gracefully handles `chunk.usage = None` → `tokens_used: 0` |
| `purge_expired()` on token blacklist never called | Must be triggered by a scheduled job or startup task — not wired up yet |

---

---

## Production Error Fixes — 2026-05-23

Three live production errors diagnosed from Railway logs and fixed across both backend and AI service.

---

### Fix 7.1 — `invalid input value for enum sessiontype: "general_bot"` (DB crash on every general chat)

**Files:**
- `Bizify-Backend/app/models/ai/chat_session.py`
- `Bizify-Backend/alembic/versions/c3d4e5f6a1b2_add_general_bot_session_type.py` *(new)*
- `bizifyAI/db/crud.py`

**Severity:** HIGH — general chat history was never saved for any user

**Problem:**
The AI service's `crud.py` tried to insert `session_type="general_bot"` (lowercase) into `chat_sessions`. But the PostgreSQL `sessiontype` enum only had: `IDEA_CHAT`, `BUSINESS_CHAT`, `STAGE_CHAT`, `GENERAL`. The value `"general_bot"` was rejected by the database on every message turn. The error was caught and swallowed (non-fatal), so requests returned 200 OK — but zero chat history was ever persisted.

**Fix (3 parts):**

1. Added `GENERAL_BOT = "GENERAL_BOT"` to `SessionType` enum in `app/models/ai/chat_session.py`
2. Created Alembic migration `c3d4e5f6a1b2` that runs:
   ```sql
   ALTER TYPE sessiontype ADD VALUE IF NOT EXISTS 'GENERAL_BOT';
   ```
3. Changed all 3 occurrences of `"general_bot"` → `"GENERAL_BOT"` in `bizifyAI/db/crud.py` (`get_or_create_general_bot_session` and `get_general_bot_history`)

**DB action completed:** SQL ran directly in Supabase SQL Editor on 2026-05-23.

---

### Fix 7.2 — `AttributeError: 'list' object has no attribute 'get'` in `OneProfileAnalysis.py` (pipeline crash for new users)

**Files:**
- `bizifyAI/agents/generalBot.py`
- `bizifyAI/agents/OneProfileAnalysis.py`

**Severity:** CRITICAL — the new-user pipeline (profile → problems → idea) crashed for every user whose questionnaire was stored as a raw list

**Problem:**
When a new user asked the general bot for an idea, `_run_new_user_pipeline_inline()` called `crud.get_questionnaire_from_profile()` which reads `user_profiles.questionnaire_json` from the database. For some production users this field contained the raw `QuestionnaireAnswer` list that the frontend submits (`[{field: "Q_q1", choices: [...], multi: false}, ...]`) instead of the processed `{user_profile: {...}, career_profile: {...}}` dict. The raw list was passed directly to `run_profile_analysis()`, which called `questionnaire.get("user_profile", {})` — crashing because lists don't have `.get()`.

**Fix (2 parts):**

1. **`agents/generalBot.py`** — Added `_normalize_questionnaire(raw)` helper function that:
   - Returns the raw value unchanged if it's already a dict (normal case)
   - Converts a list of `QuestionnaireAnswer` objects → `{user_profile: {...}, career_profile: {...}}` dict using the same field mapping as `profile_service.submit_full_questionnaire()` in the backend
   - Added guard in `_run_new_user_pipeline_inline()`: if normalization yields no usable `user_profile`, returns a friendly message instead of crashing

2. **`agents/OneProfileAnalysis.py`** — Added type guard before line 39:
   ```python
   if not isinstance(questionnaire, dict):
       raise ValueError(f"questionnaire must be a dict — got {type(questionnaire).__name__}")
   ```
   Gives a clear, readable error if a non-dict ever reaches this function in the future.

---

### Fix 7.3 — 5 AI GET endpoints would return 500 (wrong response schema field names)

**File:** `Bizify-Backend/app/schemas/ai_pipeline.py`

**Severity:** HIGH — Competition, Idea Strategy, Functions List, MVP Planning, and Unit Economics GET endpoints would crash with a response validation error

**Problem:**
The backend's Pydantic response schemas had field names that didn't match what the AI service actually returns. FastAPI validates the response dict against the `response_model` — if a required field is missing, it raises a 500 `ResponseValidationError`. The AI service routes return the data under snake_case keys matching the section name, but the schemas used different abbreviated names:

| Schema class | Wrong field (was) | Correct field (fixed to) |
|---|---|---|
| `AICompetitionResponse` | `competitors: list` | `competition: dict` |
| `AIIdeaStrategyResponse` | `strategy: dict` | `idea_strategy: dict` |
| `AIFunctionsListResponse` | `functions: list` | `functions_list: dict` |
| `AIMVPPlanningResponse` | `mvp: dict` | `mvp_planning: dict` |
| `AIUnitEconomicsResponse` | `economics: dict` | `unit_economics: dict` |

**Fix:**
All 5 schema classes updated to use the correct field names. The frontend's `useAiPipeline.ts` `SECTION_RESPONSE_KEYS` was already using the correct keys — only the backend schemas were wrong.

---

### Fix 7.4 — `TAVILY_API_KEY` missing from Railway AI service environment

**File:** Railway environment variables (AI service)

**Severity:** MEDIUM — all agents fell back to Serper search (lower quality results)

**Problem:**
`TAVILY_API_KEY` and `GROQ_EXTRACTION_MODEL` were in the local `.env` file but were never added to the Railway production environment. Every search triggered the fallback path.

**Fix:**
Added both variables to the Railway AI service environment:
- `TAVILY_API_KEY = tvly-dev-...`
- `GROQ_EXTRACTION_MODEL = llama-3.1-8b-instant`

---

## Files Changed — 2026-05-23

### `Bizify-Backend` (backend)

| File | Change |
|---|---|
| `app/models/ai/chat_session.py` | Added `GENERAL_BOT = "GENERAL_BOT"` to `SessionType` enum |
| `app/schemas/ai_pipeline.py` | Fixed field names in 5 response schemas (competition, idea_strategy, functions_list, mvp_planning, unit_economics) |
| `alembic/versions/c3d4e5f6a1b2_add_general_bot_session_type.py` | **NEW** — migration to add `GENERAL_BOT` to PostgreSQL `sessiontype` enum |

### `bizifyAI` (AI service)

| File | Change |
|---|---|
| `agents/generalBot.py` | Added `_normalize_questionnaire()` + guard in `_run_new_user_pipeline_inline()` to handle raw list questionnaire format |
| `agents/OneProfileAnalysis.py` | Added type guard before `questionnaire.get()` call |
| `db/crud.py` | Changed `"general_bot"` → `"GENERAL_BOT"` in all 3 places |

---

*Last updated: 2026-05-23*
