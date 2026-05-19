# Bizify Frontend Integration Handoff

> **This file is the single source of truth for the frontend AI agent.**
> Every endpoint, shape, flow, and warning documented here comes directly
> from reading the actual backend and AI service source code.

---

## Changelog

| Date | What changed | Why it matters to the frontend |
|------|-------------|-------------------------------|
| 2026-05-19 | **`tokens_used` added to all streaming chat `done` events** | Every `{"type": "done"}` SSE event now includes `"tokens_used": <number>` — use it to show the user how many tokens each reply consumed |
| 2026-05-19 | **`tokens_used` added to `POST /ai/chat` response** | The non-streaming idea chat response now includes `"tokens_used": <number>` at the top level |
| 2026-05-19 | **Usage quota now correctly counted for streaming and general-chat** | Previously `*/chat/stream` and `/general-chat` endpoints did not increment the usage counter — they now do. Quota display will be more accurate. |
| 2026-05-18 | **Rate limiting added** to all auth endpoints | Frontend must handle `429 Too Many Requests` from `/auth/*` endpoints; show "try again in a moment" |
| 2026-05-18 | **Usage quota: GET requests no longer consume quota** | Reading `/ai/customers`, `/ai/business-model`, etc. is now free; only POST (generate/chat/regenerate) counts |
| 2026-05-18 | **AI GET endpoint response schemas removed** | The Swagger docs no longer show response schemas for GET AI endpoints — use the shapes documented in this file instead |
| 2026-05-18 | **Paymob payment flow: subscription is now PENDING until webhook** | After calling `POST /billing/paymob/subscribe`, the user does NOT immediately have AI access. Frontend must poll or wait for confirmation before unlocking AI features |
| 2026-05-18 | **Password reset now invalidates all existing tokens** | After a successful password reset, all devices are logged out. Frontend should redirect to login after `POST /auth/reset-password` returns success |
| 2026-05-18 | **`test-email` endpoint is now admin-only and hidden from Swagger** | No frontend action needed — endpoint was never meant to be called by the frontend |

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Environment & Config](#2-environment--config)
3. [Authentication](#3-authentication)
4. [TypeScript Interfaces (All Models)](#4-typescript-interfaces-all-models)
5. [API Reference — Auth](#5-api-reference--auth)
6. [API Reference — Profile & Onboarding](#6-api-reference--profile--onboarding)
7. [API Reference — Ideas](#7-api-reference--ideas)
8. [API Reference — Groups / Teams](#8-api-reference--groups--teams)
9. [API Reference — Notifications](#9-api-reference--notifications)
10. [API Reference — AI Pipeline](#10-api-reference--ai-pipeline)
11. [AI Integration: Full Flow](#11-ai-integration-full-flow)
12. [SSE Streaming Guide](#12-sse-streaming-guide)
13. [Feature Flows (Step-by-Step)](#13-feature-flows-step-by-step)
14. [Error Handling Reference](#14-error-handling-reference)
15. [Critical Warnings](#15-critical-warnings)

---

## 1. Architecture Overview

```
Browser / Mobile App
        │
        ▼
  Backend (FastAPI)           ← frontend talks ONLY to this
  https://<backend-host>/api/v1/
        │
        ▼
  AI Service (FastAPI)        ← backend proxies AI calls here
  https://bizifyai-production.up.railway.app/pipeline/
        │
        ▼
  PostgreSQL (shared DB)
```

**The frontend NEVER calls the AI service directly.**
All AI endpoints are proxied through `/api/v1/ai/*` on the backend.

The backend handles:
- JWT authentication (all requests need `Authorization: Bearer <token>`)
- Subscription/usage gating on all `/api/v1/ai/*` endpoints
- User ID injection (frontend never needs to pass `user_id`)

---

## 2. Environment & Config

```
BACKEND_BASE_URL=https://<your-backend-host>
API_PREFIX=/api/v1
```

### Required headers on every authenticated request

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Token lifetime

- **7 days** (`ACCESS_TOKEN_EXPIRE_MINUTES = 10080`)
- No refresh token endpoint exists — redirect to login on 401

---

## 3. Authentication

### How it works

1. User registers or logs in
2. Backend returns `{ access_token, token_type: "bearer" }`
3. Frontend stores the token (localStorage or memory)
4. Every subsequent request includes `Authorization: Bearer <token>`
5. Session inactivity timeout: **240 minutes** (server-side check)
6. Session warning threshold: **5 minutes** before timeout

### Token validation rules (server enforces all of these)

- Token must not be blacklisted (logout revokes it)
- User must be active (`is_active = true`)
- User must be verified (`is_verified = true`) for most operations
- Password change invalidates old tokens
- Account lock check (after failed logins)

---

## 4. TypeScript Interfaces (All Models)

### User

```typescript
type UserRole = "ADMIN" | "USER" | "ENTREPRENEUR" | "MENTOR" | "SUPPLIER" | "MANUFACTURER";

interface User {
  id: string;           // UUID
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;   // ISO datetime
  updated_at: string;   // ISO datetime
}
```

### Token (auth response)

```typescript
interface Token {
  access_token: string;
  token_type: "bearer";
}
```

### UserProfile

```typescript
type GuideStatus = "NOT_STARTED" | "COMPLETED" | "POSTPONED" | "SKIPPED";

interface UserProfile {
  id: string;             // UUID
  user_id: string;        // UUID → users.id
  bio: string | null;
  skills_json: Skill[] | null;
  questionnaire_json: QuestionnaireData | null;
  guide_status: GuideStatus;
  onboarding_completed: boolean;
  updated_at: string | null;
}

interface Skill {
  id: string;
  name: string;
  rating: number;    // 1-5
}
```

### Questionnaire Data (stored in `questionnaire_json`)

```typescript
interface QuestionnaireData {
  user_profile: {
    curiosity_domain: string;          // e.g. "Art & Design"
    experience_level: string;          // e.g. "Beginner"
    business_interests: string[];      // e.g. ["Marketplace"]
    target_region: string;             // e.g. "MENA", "Global", "Egypt"
    founder_setup: string;             // e.g. "Solo", "Co-founder"
    risk_tolerance: string;            // e.g. "Low", "Moderate"
  };
  career_profile: {
    free_day_preferences: string[];
    preferred_work_types: string[];
    problem_solving_styles: string[];
    preferred_work_environments: string[];
    desired_impact: string[];
  };
}
```

### QuestionnaireAnswer (what you POST)

```typescript
interface QuestionnaireAnswer {
  field: string;             // e.g. "Q_q1", "career_q1_free_day"
  question?: string;         // optional human-readable question text
  multi: boolean;            // true if multiple choices allowed
  choices: string[];         // selected answer(s)
  label?: string;            // optional display label
}
```

### Questionnaire field → stored key mapping

| field            | stored key in questionnaire_json    |
|------------------|--------------------------------------|
| `Q_q1`           | `user_profile.curiosity_domain`      |
| `Q_q2`           | `user_profile.experience_level`      |
| `Q_q3`           | `user_profile.business_interests`    |
| `Q_q4`           | `user_profile.target_region`         |
| `Q_q5`           | `user_profile.founder_setup`         |
| `Q_q6_risk`      | `user_profile.risk_tolerance`        |
| `career_q1_free_day`     | `career_profile.free_day_preferences`    |
| `career_q2_work_type`    | `career_profile.preferred_work_types`    |
| `career_q3_problem_type` | `career_profile.problem_solving_styles`  |
| `career_q4_environment`  | `career_profile.preferred_work_environments` |
| `career_q5_impact`       | `career_profile.desired_impact`          |

### Idea

```typescript
interface Idea {
  id: string;                   // UUID
  owner_id: string;             // UUID → users.id
  business_id: string | null;
  title: string | null;
  description: string | null;
  status: "draft" | "active" | "archived";
  ai_score: number | null;
  budget: number | null;
  skills: Record<string, any>[] | null;
  feasibility: number | null;
  is_score_outdated: boolean;
  is_archived: boolean;
  archived_at: string | null;
  converted_at: string | null;
  created_at: string;
  updated_at: string;
}
```

### AI Pipeline Status Response

```typescript
interface PipelineStatus {
  user_id: string;
  status: "pending" | "running" | "done" | "error" | "problems_done";
  current_step: string | null;
  profile_ready: boolean;
  problems_ready: boolean;
  intake_ready: boolean;
  idea_ready: boolean;
  customers_ready: boolean;
  competition_ready: boolean;
  market_potential_ready: boolean;
  idea_strategy_ready: boolean;
  business_model_ready: boolean;
  functions_list_ready: boolean;
  mvp_planning_ready: boolean;
  unit_economics_ready: boolean;
  go_to_market_ready: boolean;
  pipeline_complete: boolean;
  error: string | null;
}
```

### General Chat Response

```typescript
interface GeneralChatResponse {
  user_id: string;
  reply: string;
  intent: string;        // "run_section" | "chat_about_data" | "pipeline_status" | "general_startup_chat" | "confirm_action" | "decline_action" | "out_of_scope" | "refine_section"
  section: string | null;
  action: string;        // "answered" | "ran_sections" | "needs_confirmation" | "declined" | "status" | "error"
  route_to_trigger: null;
  trigger_needed: false;
  chat_history_length: number;
}
```

### SSE Stream Token Event

```typescript
// Every chunk from a streaming endpoint is one of:
interface SSETokenEvent {
  type: "token";
  content: string;    // partial text to append to the UI
}

interface SSEThinkingEvent {
  type: "token";
  content: "Give me a moment while I work on that for you...";
}

interface SSEReplaceEvent {
  type: "replace";
  content: string;    // replace the entire thinking message with this
}

interface SSEDoneEvent {
  type: "done";
  tokens_used: number;        // always present — Groq tokens consumed by this reply
  intent?: string;
  action?: string;
  route_to_trigger?: null;
  trigger_needed?: false;
  chat_history_length?: number;
}
```

---

## 5. API Reference — Auth

Base path: `POST /api/v1/auth/`

---

### Register

```http
POST /api/v1/users/register
Content-Type: application/json
```

**Request body:**

```json
{
  "email": "founder@example.com",
  "full_name": "Sara Ahmed",
  "password": "Password1!",
  "confirm_password": "Password1!",
  "questionnaire_answers": []
}
```

**Password rules:** min 8 chars, at least 1 digit, 1 uppercase, 1 lowercase.

**Response `201`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "founder@example.com",
  "full_name": "Sara Ahmed",
  "role": "ENTREPRENEUR",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**After registration:** user receives OTP by email. Must verify before login works fully.

---

### Rate Limits on Auth Endpoints

All auth endpoints are rate-limited per IP address. Exceeding the limit returns `429 Too Many Requests`.

| Endpoint | Limit |
|----------|-------|
| `POST /auth/login` | 10 / minute |
| `POST /auth/google/callback` | 10 / minute |
| `POST /auth/verify-otp` | 10 / minute |
| `POST /auth/resend-verification-otp` | **3 / minute** |
| `POST /auth/forgot-password` | **3 / minute** |
| `POST /auth/verify-reset-code` | 10 / minute |
| `POST /auth/reset-password` | 5 / minute |

**429 response shape:**
```json
{ "error": "Rate limit exceeded: 3 per 1 minute" }
```

---

### Login

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
```

**Request body (form-encoded, NOT JSON):**

```
username=founder@example.com&password=Password1!
```

> **WARNING:** This endpoint uses `application/x-www-form-urlencoded`, not JSON.
> Use `URLSearchParams` or set `Content-Type: application/x-www-form-urlencoded`.

**Response `200`:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error `401`** (wrong credentials):
```json
{ "detail": "Incorrect email or password" }
```

**Error `403`** (account locked):
```json
{ "detail": "Account is temporarily locked. Try again in X minutes." }
```

---

### Google OAuth

```http
GET /api/v1/auth/google/url
```

Returns the Google login URL. Redirect the user there.

```json
{ "url": "https://accounts.google.com/o/oauth2/auth?..." }
```

After Google redirects back with a `code`:

```http
POST /api/v1/auth/google/callback
Content-Type: application/json

{ "code": "<google_auth_code>" }
```

**Response:** Same as login — `{ access_token, token_type }`.

---

### Verify OTP (email verification)

```http
POST /api/v1/auth/verify-otp
Content-Type: application/json

{
  "email": "founder@example.com",
  "otp_code": "123456"
}
```

**Response `200`:** `{ "message": "Account verified successfully" }`

---

### Resend Verification OTP

```http
POST /api/v1/auth/resend-verification-otp
Content-Type: application/json

{ "email": "founder@example.com" }
```

---

### Forgot Password

```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{ "email": "founder@example.com" }
```

**Response:** Always `200` (even if email not found, to prevent enumeration).

---

### Verify Reset Code

```http
POST /api/v1/auth/verify-reset-code
Content-Type: application/json

{
  "email": "founder@example.com",
  "otp_code": "654321"
}
```

---

### Reset Password

```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "email": "founder@example.com",
  "otp_code": "654321",
  "new_password": "NewPassword1!"
}
```

> **Token invalidation:** A successful password reset sets `last_password_change` on the user record. All previously issued tokens (other devices, sessions) are immediately invalidated on their next request. **The frontend should clear the stored token and redirect to login after this call succeeds**, even if the user is already logged in on the device initiating the reset.


---

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

**Response:** `{ "message": "Logged out successfully" }`

---

### Session Status

```http
GET /api/v1/auth/session-status
Authorization: Bearer <token>
```

**Response:**

```json
{
  "is_active": true,
  "remaining_minutes": 185.3,
  "warning_threshold": 5
}
```

Poll this every 60 seconds. When `remaining_minutes < warning_threshold`, show a "Session expiring" warning. When `remaining_minutes <= 0`, redirect to login.

---

### Keep Session Alive (ping)

```http
POST /api/v1/auth/ping
Authorization: Bearer <token>
```

Call this whenever the user is active (mouse move, click, keypress). Resets the inactivity timer.

---

## 6. API Reference — Profile & Onboarding

Base path: `/api/v1/profile/`
All endpoints require `Authorization: Bearer <token>`.

---

### Get My Profile

```http
GET /api/v1/profile/
Authorization: Bearer <token>
```

**Response `200`:**

```json
{
  "id": "...",
  "user_id": "550e8400...",
  "bio": null,
  "skills_json": [
    { "id": "abc-123", "name": "Python", "rating": 3 }
  ],
  "questionnaire_json": {
    "user_profile": {
      "curiosity_domain": "Art & Design",
      "experience_level": "Beginner",
      "business_interests": ["Marketplace"],
      "target_region": "MENA",
      "founder_setup": "Solo",
      "risk_tolerance": "Low"
    },
    "career_profile": {
      "free_day_preferences": ["Learning new skills"],
      "preferred_work_types": ["Working with ideas"],
      "problem_solving_styles": ["Research and analyze data"],
      "preferred_work_environments": ["Remote"],
      "desired_impact": ["Make strong income"]
    }
  },
  "guide_status": "NOT_STARTED",
  "onboarding_completed": false,
  "updated_at": "2024-01-15T10:30:00"
}
```

---

### Submit Questionnaire

```http
POST /api/v1/profile/questionnaire
Authorization: Bearer <token>
Content-Type: application/json

[
  {
    "field": "Q_q1",
    "question": "What domain are you curious about?",
    "multi": false,
    "choices": ["Art & Design"],
    "label": "Curiosity Domain"
  },
  {
    "field": "Q_q3",
    "question": "What type of business interests you?",
    "multi": true,
    "choices": ["Marketplace"],
    "label": "Business Interests"
  },
  {
    "field": "Q_q4",
    "multi": false,
    "choices": ["MENA"]
  },
  {
    "field": "Q_q5",
    "multi": false,
    "choices": ["Solo founder"]
  },
  {
    "field": "Q_q6_risk",
    "multi": false,
    "choices": ["Low risk - minimal investment"]
  },
  {
    "field": "career_q1_free_day",
    "multi": true,
    "choices": ["Learning new skills", "Exploring business ideas"]
  },
  {
    "field": "career_q2_work_type",
    "multi": true,
    "choices": ["Working with ideas"]
  },
  {
    "field": "career_q5_impact",
    "multi": true,
    "choices": ["Make strong income"]
  }
]
```

**Response `200`:**

```json
{
  "user_profile": {
    "curiosity_domain": "Art & Design",
    "experience_level": null,
    "business_interests": ["Marketplace"],
    "target_region": "MENA",
    "founder_setup": "Solo founder",
    "risk_tolerance": "low risk"
  },
  "career_profile": {
    "free_day_preferences": ["Learning new skills", "Exploring business ideas"],
    "preferred_work_types": ["Working with ideas"],
    "problem_solving_styles": [],
    "preferred_work_environments": [],
    "desired_impact": ["Make strong income"]
  }
}
```

> **After submitting:** call `POST /api/v1/profile/complete` to finalize onboarding, then call `POST /api/v1/ai/run` to trigger the AI pipeline.

---

### Get Questionnaire (raw JSON)

```http
GET /api/v1/profile/questionnaire
Authorization: Bearer <token>
```

Returns the raw `questionnaire_json` stored in the profile.

---

### Complete Onboarding

```http
POST /api/v1/profile/complete
Authorization: Bearer <token>
```

**Response:** `{ "status": "success", "message": "Onboarding finalized" }`

---

### Skip Questionnaire

```http
POST /api/v1/profile/skip
Authorization: Bearer <token>
```

---

### Restart Questionnaire

```http
POST /api/v1/profile/restart
Authorization: Bearer <token>
```

Clears `questionnaire_json` and resets `onboarding_completed` to `false`.

---

### List User Skills

```http
GET /api/v1/profile/skills
Authorization: Bearer <token>
```

**Response:**

```json
[
  { "id": "abc-123", "name": "Python", "rating": 3 },
  { "id": "def-456", "name": "Marketing", "rating": 4 }
]
```

---

### Add Skill

```http
POST /api/v1/profile/skills
Authorization: Bearer <token>
Content-Type: application/json

{ "skill_name": "Digital Marketing" }
```

**Response:** `{ "id": "uuid", "name": "Digital Marketing", "rating": 3 }`

---

### Delete Skill

```http
DELETE /api/v1/profile/skills/{skill_id}
Authorization: Bearer <token>
```

**Response:** `204 No Content`

---

### Get Skills JSON (raw)

```http
GET /api/v1/profile/skills/json
Authorization: Bearer <token>
```

---

### Update Skills JSON (raw)

```http
POST /api/v1/profile/skills/json
Authorization: Bearer <token>
Content-Type: application/json

{ "skills": [...] }
```

---

### Search Predefined Skills

```http
GET /api/v1/profile/skills/search?q=python
Authorization: Bearer <token>
```

**Response:** `["Python", "PyTorch", "PySpark"]`

---

### List Skill Categories

```http
GET /api/v1/profile/skill-categories
Authorization: Bearer <token>
```

**Response:**

```json
[
  "Programming & Development",
  "Data & Analytics",
  "Design & UX",
  "Marketing & Sales",
  "Business & Management",
  "Finance & Accounting",
  "Operations & Logistics",
  "Customer Support",
  "AI & Machine Learning"
]
```

---

## 7. API Reference — Ideas

Base path: `/api/v1/ideas/`
All require `Authorization: Bearer <token>`.

---

### Get Ideas (with filters)

```http
GET /api/v1/ideas/?min_budget=100&max_budget=5000&skills=Python,React&feasibility=0.7&sort_by=ai_score&sort_order=desc
Authorization: Bearer <token>
```

**Query params (all optional):**

| param | type | description |
|-------|------|-------------|
| `min_budget` | float | minimum budget filter |
| `max_budget` | float | maximum budget filter |
| `skills` | string | comma-separated skill names |
| `feasibility` | float | minimum feasibility score |
| `sort_by` | string | `created_at` \| `budget` \| `feasibility` \| `ai_score` |
| `sort_order` | string | `asc` \| `desc` |

**Response:** Array of `Idea` objects.

---

### Create Idea

```http
POST /api/v1/ideas/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Art Marketplace",
  "description": "A platform for independent artists..."
}
```

**Response:** `Idea` object.

---

### Get Archived Ideas

```http
GET /api/v1/ideas/archived
Authorization: Bearer <token>
```

---

### Archive Idea

```http
PATCH /api/v1/ideas/{idea_id}/archive
Authorization: Bearer <token>
```

---

### Unarchive Idea

```http
PATCH /api/v1/ideas/{idea_id}/unarchive
Authorization: Bearer <token>
```

---

## 8. API Reference — Groups / Teams

Base path: `/api/v1/groups/`
All require `Authorization: Bearer <token>`.

---

### Create Group

```http
POST /api/v1/groups
Content-Type: application/json

{ "name": "My Startup Team", "description": "..." }
```

---

### List Groups

```http
GET /api/v1/groups
```

---

### Update Group

```http
PATCH /api/v1/groups/{group_id}
```

---

### Delete Group

```http
DELETE /api/v1/groups/{group_id}
```

---

### Invite to Group

```http
POST /api/v1/groups/{group_id}/invites
Content-Type: application/json

{ "email": "cofounder@example.com" }
```

---

### Accept Group Invite

```http
POST /api/v1/groups/invites/accept
Content-Type: application/json

{ "token": "<invite_token>" }
```

---

### Request to Join Group

```http
POST /api/v1/groups/{group_id}/join-requests
```

---

### Handle Join Request

```http
POST /api/v1/groups/join-requests/{request_id}/handle
Content-Type: application/json

{ "action": "approve" | "reject" }
```

---

### List Group Members

```http
GET /api/v1/groups/{group_id}/members
```

---

### Group Messages (WebSocket)

```ws
WS /api/v1/groups/{group_id}/ws?token=<access_token>
```

---

## 9. API Reference — Notifications

Base path: `/api/v1/notifications/`
All require `Authorization: Bearer <token>`.

---

### Get Notifications

```http
GET /api/v1/notifications/
```

---

## 10. API Reference — AI Pipeline

Base path: `/api/v1/ai/`

> **All endpoints require:**
> - `Authorization: Bearer <token>`
> - User must have an active subscription with `ai_analysis: true` feature
> - **Error `403`** if no AI access: `{"detail": "Your current plan does not include AI analysis features."}`
> - **Error `429`** if monthly limit exceeded: `{"detail": "AI request limit reached (N/M). Please upgrade your plan or wait for your limit to reset."}`

> **CRITICAL:** The frontend **never** sends `user_id` in the request body.
> The backend injects it automatically from the JWT token.

> **Quota rules (updated 2026-05-18):**
> - Only **POST** requests (generate, regenerate, chat) consume quota
> - **GET** requests (reading saved sections) are **free** — do not consume quota
> - **Failed AI calls** (AI service down, timeout, AI-side error) are **free** — quota is only charged on a confirmed `2xx` success
> - The quota counter is per-user and per-plan (not per-IP)

---

### Check AI Health (no auth required)

```http
GET /api/v1/ai/health
```

**Response:** `{ "status": "ok", "timestamp": 1234567890 }`

---

### Get Pipeline Status

```http
GET /api/v1/ai/status
Authorization: Bearer <token>
```

**Response:**

```json
{
  "user_id": "550e8400...",
  "status": "done",
  "current_step": null,
  "profile_ready": true,
  "problems_ready": true,
  "intake_ready": false,
  "idea_ready": true,
  "customers_ready": true,
  "competition_ready": false,
  "market_potential_ready": false,
  "idea_strategy_ready": false,
  "business_model_ready": false,
  "functions_list_ready": false,
  "mvp_planning_ready": false,
  "unit_economics_ready": false,
  "go_to_market_ready": false,
  "pipeline_complete": false,
  "error": null
}
```

---

### Trigger AI Pipeline (new user)

```http
POST /api/v1/ai/run
Authorization: Bearer <token>
```

**Request body:** empty `{}`

**Response `202`:**

```json
{
  "user_id": "550e8400...",
  "status": "pending",
  "message": "Pipeline started. Poll /pipeline/status/{user_id} for progress.",
  "poll_url": "/pipeline/status/550e8400..."
}
```

Poll `GET /api/v1/ai/status` every 3-5 seconds until `idea_ready: true`.

---

### Get Generated Idea

```http
GET /api/v1/ai/idea
Authorization: Bearer <token>
```

**Response:**

```json
{
  "user_id": "550e8400...",
  "current_idea": "💡 IDEA: ArtNest Marketplace\n...",
  "chat_history": []
}
```

> **Note:** `current_idea` is a **plain text string** (formatted with the idea template), NOT a JSON object.

---

### Chat About Idea

```http
POST /api/v1/ai/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Can you make the business model more focused on MENA?",
  "history": []
}
```

**Response:**

```json
{
  "user_id": "550e8400...",
  "reply": "Sure! Here's a revised version...",
  "chat_history_length": 2,
  "tokens_used": 847
}
```

> `tokens_used` is the total Groq token count (prompt + completion) for this reply. Use it to display per-message token cost in the UI.

---

### Chat About Idea — Streaming

```http
POST /api/v1/ai/chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Make the idea more focused on Egypt",
  "history": []
}
```

Returns SSE stream. See [Section 12](#12-sse-streaming-guide).

---

### General Chat (AI assistant)

```http
POST /api/v1/ai/general-chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Run my customer analysis",
  "history": [
    { "role": "user", "content": "What is my idea?" },
    { "role": "assistant", "content": "Your idea is..." }
  ]
}
```

**Response:**

```json
{
  "user_id": "550e8400...",
  "reply": "I've generated your customer analysis! Here are the key insights:\n\n...",
  "intent": "run_section",
  "section": "customers",
  "action": "ran_sections",
  "route_to_trigger": null,
  "trigger_needed": false,
  "chat_history_length": 4
}
```

**Intent values and what to do:**

| intent | action | what it means |
|--------|--------|---------------|
| `run_section` | `ran_sections` | AI ran an analysis section; refresh that section's data |
| `run_section` | `needs_confirmation` | AI is asking user to confirm running prerequisites |
| `chat_about_data` | `answered` | AI answered from existing data |
| `general_startup_chat` | `answered` | General startup advice |
| `pipeline_status` | `status` | AI summarised what's done |
| `confirm_action` | `ran_sections` | User confirmed, AI ran sections |
| `decline_action` | `declined` | User declined |
| `out_of_scope` | `declined` | Off-topic question |

**Invisible pending marker:** When `action = "needs_confirmation"`, the `reply` string contains an invisible HTML comment like `<!--PENDING:customers,competition,market_potential-->`. You MUST pass the full `reply` back in `history` on the next turn so the bot can detect the user's confirm/decline.

---

### General Chat — Streaming

```http
POST /api/v1/ai/general-chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{ "message": "...", "history": [...] }
```

For `run_section` / `confirm_action` intents, the stream emits:
1. `{"type": "token", "content": "Give me a moment..."}` — immediately
2. Long pause (AI runs agents)
3. `{"type": "replace", "content": "<full reply>"}` — replace the thinking text
4. `{"type": "done", "intent": "...", "action": "..."}` — stream complete

For all other intents: normal token-by-token streaming.

---

### Explain a Section

```http
POST /api/v1/ai/explain
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "What does my LTV/CAC ratio mean?",
  "history": [],
  "section": "unit_economics"
}
```

**`section` values:** `profile` | `problems` | `idea` | `customers` | `competition` | `market_potential` | `idea_strategy` | `business_model` | `functions_list` | `mvp_planning` | `unit_economics` | `go_to_market`

**Response:**

```json
{
  "user_id": "550e8400...",
  "reply": "Your LTV/CAC ratio of 2.8x means...",
  "section_used": "unit_economics",
  "data_available": ["idea", "customers", "business_model", "unit_economics"],
  "chat_history_length": 2
}
```

---

### Idea Intake (returning users)

For users who already have an idea concept and want to skip the full onboarding pipeline.

```http
POST /api/v1/ai/idea-intake
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "I want to build a marketplace for handmade art in Egypt",
  "history": []
}
```

**Response (idea clear enough):**

```json
{
  "user_id": "550e8400...",
  "status": "ready",
  "intake": {
    "idea_summary": "A marketplace for handmade art in Egypt",
    "target_users": ["art lovers", "collectors"],
    "industry": "Art & Design Marketplace",
    "problem_assumption": "Buyers struggle to find authentic handmade art online in Egypt",
    "solution_assumption": "A curated marketplace connecting buyers to verified artists",
    "business_model": "Commission",
    "region": "Egypt",
    "keywords_for_problem_discovery": ["handmade art marketplace Egypt problems", "..."],
    "unclear_questions": []
  },
  "reply": "Your idea is clear! I'm now researching real problems around it..."
}
```

**Response (idea too vague):**

```json
{
  "user_id": "550e8400...",
  "status": "needs_clarification",
  "reply": "I'd love to help! A few quick questions: Who are your target customers? What specific problem are you solving? What's your target region?",
  "questions": ["Who are your target customers?", "What problem do you solve?"],
  "history": [
    { "role": "user", "content": "I want to build something for art" },
    { "role": "assistant", "content": "..." }
  ]
}
```

When `status = "needs_clarification"`, pass `history` from the response back in the next request.

---

### Trigger Problem Discovery (after intake)

After `idea-intake` returns `status: "ready"`:

```http
POST /api/v1/ai/idea-intake/run-problems
Authorization: Bearer <token>
```

**Response `202`:**

```json
{
  "user_id": "550e8400...",
  "status": "pending",
  "message": "Problem discovery started...",
  "poll_url": "/pipeline/status/550e8400..."
}
```

Poll status until `problems_ready: true`, then call `POST /api/v1/ai/idea-intake/start-chat`.

---

### Start Idea Chat (after intake + problems)

```http
POST /api/v1/ai/idea-intake/start-chat
Authorization: Bearer <token>
```

**Request body:** empty `{}`

**Response:**

```json
{
  "user_id": "550e8400...",
  "status": "done",
  "current_idea": "💡 IDEA: ArtNest Egypt...",
  "chat_history": [...],
  "message": "Idea chat is ready. Continue with /pipeline/chat."
}
```

---

### Get Idea Intake

```http
GET /api/v1/ai/idea-intake
Authorization: Bearer <token>
```

---

## Analysis Sections (Agents 4-12)

Each section follows the same pattern. Replace `{section}` with one of:

| section | URL slug |
|---------|----------|
| Customer Analysis | `customers` |
| Competition Analysis | `competition` |
| Market Potential | `market-potential` |
| Idea Strategy | `idea-strategy` |
| Business Model | `business-model` |
| Product Functions List | `functions-list` |
| MVP Planning | `mvp-planning` |
| Unit Economics | `unit-economics` |
| Go-To-Market Plan | `go-to-market` |

---

### Generate / Regenerate a Section

```http
POST /api/v1/ai/{section}
Authorization: Bearer <token>
```

**Request body:** empty `{}`

**Error `425`** if prerequisites not met:
```json
{ "detail": "Idea not ready. Complete the pipeline first." }
```

**Response (customers example):**

```json
{
  "user_id": "550e8400...",
  "status": "done",
  "customers": {
    "customer_segments": [
      {
        "id": "CS1",
        "name": "Art Enthusiast Collectors",
        "description": "...",
        "pain_intensity": "high",
        "size_estimate": "50,000 active buyers in MENA",
        "willingness_to_pay": "high",
        "why_they_care": "...",
        "behavior": "...",
        "where_to_find": ["Instagram", "Facebook art groups"]
      }
    ],
    "primary_segment": { "id": "CS1", "reason": "..." },
    "catwoe": { "customers": "...", "actors": "...", ... },
    "personas": [...],
    "acquisition_channels": [...],
    "early_adopter_profile": "Art lovers aged 25-40 in Cairo who follow local artists on Instagram",
    "summary": "...",
    "source_mode": "web_sourced",
    "sources_used": 8,
    "sources_list": [{ "url": "https://...", "title": "..." }]
  }
}
```

**Response key names by section:**

| URL slug | response key |
|----------|-------------|
| `customers` | `customers` |
| `competition` | `competition` |
| `market-potential` | `market_potential` |
| `idea-strategy` | `idea_strategy` |
| `business-model` | `business_model` |
| `functions-list` | `functions_list` |
| `mvp-planning` | `mvp_planning` |
| `unit-economics` | `unit_economics` |
| `go-to-market` | `go_to_market` |

---

### Regenerate with Custom Instruction

```http
POST /api/v1/ai/{section}/regenerate-custom
Authorization: Bearer <token>
Content-Type: application/json

{
  "custom_prompt": "Focus more on the Egyptian market and adjust the target customer to be younger, 18-25"
}
```

**Response:** Same shape as the generate endpoint.

---

### Get Saved Section

```http
GET /api/v1/ai/{section}
Authorization: Bearer <token>
```

**Response:**

```json
{
  "user_id": "550e8400...",
  "{section_key}": { ...full section data... },
  "chat_history": []
}
```

**Response key names by section (GET):**

| URL slug | response key |
|----------|-------------|
| `customers` | `customers` |
| `competition` | `competition` |
| `market-potential` | `market_potential` |
| `idea-strategy` | `idea_strategy` |
| `business-model` | `business_model` |
| `functions-list` | `functions_list` |
| `mvp-planning` | `mvp_planning` |
| `unit-economics` | `unit_economics` |
| `go-to-market` | `go_to_market` |

**Error `404`** if not generated yet:
```json
{ "detail": "No customers analysis found for this user." }
```

---

### Chat About a Section

```http
POST /api/v1/ai/{section}/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Add a segment for B2B art buyers in hotels",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**Response:**

```json
{
  "user_id": "550e8400...",
  "reply": "Here's the updated segment...\n\n```json\n{...updated section JSON...}\n```",
  "chat_history_length": 4
}
```

> The reply may contain a ` ```json ` block with updated section data. Parse it to show real-time updates in the UI.

---

### Chat — Streaming

```http
POST /api/v1/ai/{section}/chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "...",
  "history": [...]
}
```

Returns SSE. See [Section 12](#12-sse-streaming-guide).

---

### Other AI Endpoints

```http
GET /api/v1/ai/profile          # Get profile analysis
GET /api/v1/ai/problems         # Get discovered problems
GET /api/v1/ai/questionnaire    # Get raw questionnaire data

POST /api/v1/ai/rerun/profile   # Re-run profile analysis
POST /api/v1/ai/rerun/problems  # Re-run problem discovery
```

---

## 11. AI Integration: Full Flow

### Flow A: New User (first time)

```
1. User completes registration
   POST /api/v1/users/register

2. User verifies email
   POST /api/v1/auth/verify-otp

3. User logs in
   POST /api/v1/auth/login  →  store access_token

4. User submits questionnaire
   POST /api/v1/profile/questionnaire  (array of QuestionnaireAnswer)

5. User finalizes onboarding
   POST /api/v1/profile/complete

6. Frontend triggers AI pipeline
   POST /api/v1/ai/run

7. Frontend polls status every 3 seconds
   GET /api/v1/ai/status
   → Wait until idea_ready: true

8. Frontend fetches the generated idea
   GET /api/v1/ai/idea
   → current_idea is a formatted text string

9. User chats to refine the idea
   POST /api/v1/ai/chat  (or /chat/stream)

10. User wants to generate analysis sections
    → Use General Chat: POST /api/v1/ai/general-chat
    OR
    → Directly generate: POST /api/v1/ai/customers

11. Each section can be refined via chat
    POST /api/v1/ai/customers/chat
```

### Flow B: Returning User with an Idea

```
1. User logs in
   POST /api/v1/auth/login

2. User describes their idea
   POST /api/v1/ai/idea-intake  { message: "I want to build..." }

   IF status = "needs_clarification":
     - Show AI's questions in the UI
     - User answers → POST /api/v1/ai/idea-intake again with history

   IF status = "ready":
     - Continue to step 3

3. Trigger problem discovery
   POST /api/v1/ai/idea-intake/run-problems

4. Poll status
   GET /api/v1/ai/status  → wait for problems_ready: true

5. Start idea refinement chat
   POST /api/v1/ai/idea-intake/start-chat

6. Continue with analysis sections (same as Flow A step 10+)
```

### Flow C: Using the General Chat Bot

The general chat bot is the most powerful interface. It handles everything:

```javascript
// Send message
const response = await api.post('/ai/general-chat', {
  message: "Generate my customer analysis",
  history: chatHistory
});

// Always append to history for next turn
chatHistory.push(
  { role: "user", content: message },
  { role: "assistant", content: response.reply }
);

// Handle action
if (response.action === "ran_sections") {
  // Refresh the relevant section UI
  await refreshSection(response.section);
}

if (response.action === "needs_confirmation") {
  // The reply already contains the question + invisible marker
  // Just display it — next user message will be detected as confirm/decline
}
```

---

## 12. SSE Streaming Guide

All `*/stream` endpoints return `text/event-stream`.

### React implementation

```typescript
async function streamChatMessage(
  endpoint: string,
  payload: object,
  token: string,
  onToken: (text: string) => void,
  onReplace: (text: string) => void,
  onDone: (meta: object) => void
) {
  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const json = line.slice(6).trim();
      if (!json) continue;

      const event = JSON.parse(json);

      if (event.type === "token") {
        onToken(event.content);
      } else if (event.type === "replace") {
        onReplace(event.content);
      } else if (event.type === "done") {
        onDone(event);
      }
    }
  }
}
```

### Usage example

```typescript
let displayedText = "";

await streamChatMessage(
  "/api/v1/ai/general-chat/stream",
  { message: "Run my customer analysis", history: [] },
  token,
  (chunk) => {
    displayedText += chunk;
    setUiText(displayedText);      // append streaming tokens
  },
  (full) => {
    displayedText = full;
    setUiText(displayedText);      // replace "thinking..." with full reply
  },
  (meta) => {
    if (meta.action === "ran_sections") {
      refreshSection(meta.section); // reload the generated section
    }
    if (meta.tokens_used) {
      showTokenCount(meta.tokens_used); // e.g. "Reply used 847 tokens"
    }
  }
);
```

---

## 13. Feature Flows (Step-by-Step)

### Registration + Onboarding

```
1. POST /api/v1/users/register
   body: { email, full_name, password, confirm_password }
   → store nothing yet, user is unverified

2. User receives OTP email

3. POST /api/v1/auth/verify-otp
   body: { email, otp_code }
   → account verified

4. POST /api/v1/auth/login
   body: form-encoded { username: email, password }
   → store { access_token, token_type }

5. GET /api/v1/profile/
   → check onboarding_completed, guide_status

6. Show questionnaire UI

7. POST /api/v1/profile/questionnaire
   body: [ QuestionnaireAnswer, ... ]

8. POST /api/v1/profile/complete

9. POST /api/v1/ai/run
   → { status: "pending" }

10. Poll GET /api/v1/ai/status every 3s
    → wait for idea_ready: true AND status: "done"

11. GET /api/v1/ai/idea
    → show current_idea text to user
```

### Generating an Analysis Section

```
1. Check GET /api/v1/ai/status → section_ready: false

2. POST /api/v1/ai/{section}
   body: {}
   → { status: "done", {section}: { ...data... } }

   If 425: prerequisites not met → prompt user to generate prerequisites first

3. Section is now cached in DB

4. GET /api/v1/ai/{section}
   → { {section}: { ...data... }, chat_history: [] }

5. User chats to refine
   POST /api/v1/ai/{section}/chat
   body: { message, history }

6. Parse reply for ```json blocks to show live updates
```

### Password Reset

```
1. POST /api/v1/auth/forgot-password
   body: { email }

2. User receives OTP

3. POST /api/v1/auth/verify-reset-code
   body: { email, otp_code }

4. POST /api/v1/auth/reset-password
   body: { email, otp_code, new_password }
```

---

## 14. Error Handling Reference

### Standard error shape

```json
{ "detail": "Human-readable error message" }
```

### Validation error shape (422)

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "notanemail"
    }
  ]
}
```

### HTTP status codes

| Code | Meaning | Common causes |
|------|---------|-------------|
| `200` | OK | Successful GET/POST |
| `201` | Created | Registration successful |
| `202` | Accepted | Async pipeline started |
| `204` | No Content | Skill deleted |
| `400` | Bad Request | Invalid input (e.g. min_budget > max_budget); invalid/expired OTP |
| `401` | Unauthorized | Missing, invalid, or expired token; token revoked after password reset or account suspension |
| `403` | Forbidden | No subscription, AI feature disabled on plan, or non-admin accessing admin route |
| `404` | Not Found | Resource doesn't exist or section not generated yet |
| `409` | Conflict | Email already registered |
| `422` | Unprocessable Entity | Request body fails Pydantic validation (wrong types, missing fields) |
| `425` | Too Early | AI pipeline prerequisites not met (idea/problems not ready) |
| `429` | Too Many Requests | Two distinct causes: (1) **Auth rate limit** — too many requests per IP on `/auth/*`; (2) **AI quota** — monthly AI request limit reached on `/ai/*` |
| `500` | Internal Server Error | Unexpected server error (DB crash, unhandled exception) |
| `502` | Bad Gateway | PayPal or Paymob API returned an error |
| `503` | Service Unavailable | `AI_PIPELINE_API_KEY` not configured, or AI service unreachable |

### Distinguishing the two `429` sources

```typescript
// Check the detail message to know which 429 it is:
if (error.status === 429) {
  const msg = error.body?.detail ?? error.body?.error ?? "";
  if (msg.includes("Rate limit exceeded")) {
    // Auth rate limit (per IP, per minute) — auth endpoint throttle
    showToast("Too many attempts. Please wait a moment and try again.");
  } else {
    // AI monthly quota exhausted
    showToast("AI request limit reached. Upgrade your plan for more.");
    showUpgradeModal();
  }
}
```

### Frontend error handling pattern

```typescript
try {
  const data = await apiCall();
  handleSuccess(data);
} catch (error) {
  if (error.status === 401) {
    // Token expired, revoked, or invalidated (e.g. after password reset)
    clearToken();
    router.push("/login");
  } else if (error.status === 403) {
    // No subscription or AI feature not in plan
    showUpgradeModal();
  } else if (error.status === 425) {
    // Pipeline prerequisites not ready
    showToast("Please generate prerequisite sections first.");
  } else if (error.status === 429) {
    const msg = error.body?.detail ?? error.body?.error ?? "";
    if (msg.includes("Rate limit exceeded")) {
      showToast("Too many attempts. Please wait a moment and try again.");
    } else {
      showToast("AI request limit reached. Upgrade your plan for more.");
      showUpgradeModal();
    }
  } else if (error.status === 422) {
    // Validation error — show field-level errors
    showFieldErrors(error.body.detail);
  } else if (error.status === 502 || error.status === 503) {
    showToast("Payment or AI service is temporarily unavailable. Please try again.");
  } else {
    showToast("Something went wrong. Please try again.");
  }
}
```

---

## 15. Critical Warnings

### ⚠️ WARNING 1: Login uses form-encoded, NOT JSON

```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded   ← NOT application/json

body: username=email@example.com&password=MyPass1
```

Using JSON will return `422 Unprocessable Entity`.

### ⚠️ WARNING 2: Never send `user_id` from the frontend

All AI endpoints accept `user_id` in the body internally, but the **backend injects the correct `user_id` from the JWT** before forwarding. If the frontend sends a `user_id`, the backend overwrites it. This is the security model — never rely on the frontend to provide it.

### ⚠️ WARNING 3: AI pipeline is async — always poll

`POST /api/v1/ai/run` returns `202` immediately. The pipeline runs in the background. You MUST poll `GET /api/v1/ai/status` until `idea_ready: true` and `status: "done"` before trying to fetch the idea.

Recommended polling interval: **3 seconds**. Timeout after **5 minutes** and show an error.

### ⚠️ WARNING 4: Swagger response schemas for AI GET endpoints are removed — use this doc

The incorrect `response_model` annotations on GET AI endpoints (e.g. `AICustomersResponse`, `AIMVPPlanningResponse`) have been removed from the backend. They showed wrong shapes (e.g. `customers: list` when the actual value is a `dict`). The AI GET endpoints now return the raw JSON from the AI service.

Use the shapes documented in this file:

- `GET /api/v1/ai/status` → full `PipelineStatus` object (13+ fields)
- `GET /api/v1/ai/customers` → `{ user_id, customers: {...dict...}, chat_history: [] }` — `customers` is a **dict**, not a list
- `GET /api/v1/ai/competition` → `{ user_id, competition: {...dict...}, chat_history: [] }`
- `GET /api/v1/ai/idea` → `{ user_id, current_idea: string, chat_history: [] }` — `current_idea` is **plain text**, not JSON

**Never trust Swagger for GET AI endpoint shapes. Use the TypeScript interfaces in Section 4.**

### ⚠️ WARNING 5: No refresh token — redirect to login on 401

Token expires after 7 days. There is no refresh endpoint. When you receive `401`, clear the stored token and redirect to the login page.

### ⚠️ WARNING 6: Pass full history on every general-chat turn

The `<!--PENDING:section1,section2-->` marker embedded in the assistant's reply is how the bot detects pending confirmations. If you strip or omit the previous assistant messages from `history`, confirmation flows will break.

Always maintain the complete history array and pass it in full:

```typescript
// CORRECT
const response = await api.post('/ai/general-chat', {
  message: "yes go ahead",
  history: [
    { role: "user", content: "generate my business model" },
    { role: "assistant", content: "To generate your **Business Model**, I need to run 3 other analyses first:\n- Customer Analysis\n...\nShall I go ahead?<!--PENDING:customers,competition,market_potential,business_model-->" }
  ]
});

// WRONG — will lose the PENDING marker
const response = await api.post('/ai/general-chat', {
  message: "yes go ahead",
  history: []
});
```

### ⚠️ WARNING 7: Section data is nested under a key, not at the top level

When you GET a section, the data is nested:

```json
// GET /api/v1/ai/customers
{
  "user_id": "...",
  "customers": { ...full customer analysis... },   ← the data
  "chat_history": []
}

// GET /api/v1/ai/business-model
{
  "user_id": "...",
  "business_model": { ...full business model... },
  "chat_history": []
}
```

When you POST to generate a section:
```json
// POST /api/v1/ai/customers
{
  "user_id": "...",
  "status": "done",
  "customers": { ...full customer analysis... }   ← same nested key
}
```

### ⚠️ WARNING 8: Guide status enum values use ENUM NAMES (uppercase)

`guide_status` stores the Enum **name** (not value), so values are:
- `"NOT_STARTED"`
- `"COMPLETED"`
- `"POSTPONED"`
- `"SKIPPED"`

Not lowercase versions of these.

### ⚠️ WARNING 9: Onboarding pipeline auto-trigger is NOT automatic

`POST /api/v1/profile/complete` marks onboarding done but does NOT start the AI pipeline. The frontend must explicitly call `POST /api/v1/ai/run` after completing onboarding.

### ⚠️ WARNING 10: AI endpoints require a subscription

Every endpoint under `/api/v1/ai/*` (except `/ai/health` and `/ai/version-check`) requires the user's active plan to have `ai_analysis: true`. Without a subscription, all AI calls return `403`. Plan this into your billing/onboarding UX.

### ⚠️ WARNING 11: `current_idea` from the idea endpoint is plain text, not JSON

```typescript
// WRONG — will fail
const idea = response.current_idea.title;

// CORRECT — it's a formatted text string
const ideaText = response.current_idea; // "💡 IDEA: ArtNest\n─────────\nProblem it solves: ..."
setIdeaDisplay(ideaText); // render as markdown/pre-formatted text
```

### ⚠️ WARNING 12: SSE stream buffer handling

SSE chunks can be split across TCP packets. Always buffer and split on `\n\n`:

```typescript
// WRONG — will miss events that span packets
for await (const chunk of response.body) {
  const event = JSON.parse(chunk.slice(6));
}

// CORRECT — use the buffering implementation in Section 12
```

### ⚠️ WARNING 13: Questionnaire field names are strict

The `field` values in `QuestionnaireAnswer` must match exactly:

```
Q_q1, Q_q2, Q_q3, Q_q4, Q_q5, Q_q6_risk,
career_q1_free_day, career_q2_work_type, career_q3_problem_type,
career_q4_environment, career_q5_impact
```

Any unrecognised `field` value is silently ignored (not saved). Missing questionnaire fields mean the AI pipeline gets empty/null values for those inputs.

---

### ⚠️ WARNING 14: Auth endpoints are rate-limited — handle 429 gracefully

All `/api/v1/auth/*` endpoints are now throttled per IP:

- `forgot-password` and `resend-verification-otp`: **3 requests/minute**
- `login`: **10 requests/minute**
- Others: 5–10 requests/minute

When the limit is exceeded the server returns:
```json
HTTP 429
{ "error": "Rate limit exceeded: 3 per 1 minute" }
```

The frontend must catch this and show a friendly message — never silently retry in a tight loop or the user stays locked out.

```typescript
// Recommended UX
if (error.status === 429 && isAuthEndpoint(url)) {
  showToast("Too many attempts. Please wait 60 seconds and try again.");
  startCountdown(60);   // disable the button for 60s
}
```

---

### ⚠️ WARNING 15: Paymob payment — subscription is PENDING until the webhook fires

After calling `POST /api/v1/billing/paymob/subscribe`:
1. The backend creates a **PENDING** subscription (not yet active)
2. Returns an `iframe_url` — render it in an `<iframe>` so the user can enter card details
3. Paymob processes the payment and fires a webhook to the backend
4. The backend webhook handler sets the subscription to **ACTIVE**

**The user does NOT have AI access between steps 2 and 4.** Do not assume the subscription is active as soon as the iframe loads. After the iframe closes (Paymob redirects on success/failure), call `GET /api/v1/billing/subscription` to check if the subscription is now active before allowing access.

```typescript
// After Paymob iframe closes:
const checkSubscription = async () => {
  const sub = await api.get('/billing/subscription');
  if (sub.status === 'active') {
    allowAIAccess();
  } else {
    showToast("Payment is being processed. Please wait a moment.");
    setTimeout(checkSubscription, 3000); // retry after 3s
  }
};
```

---

### ⚠️ WARNING 16: Password reset invalidates all tokens on all devices

After `POST /api/v1/auth/reset-password` returns `200`, **every token previously issued to this user becomes invalid** — including the token on the device that initiated the reset. If the user is logged in while resetting their password:

1. Clear `access_token` from storage immediately after success
2. Redirect to login
3. Do not attempt any further API calls with the old token

```typescript
const resetPassword = async (email, otp, newPassword) => {
  await api.post('/auth/reset-password', { email, otp_code: otp, new_password: newPassword });
  // ← ALL tokens now invalid
  clearToken();           // remove from localStorage / memory
  router.push('/login');  // force re-login on all devices
};
```

---

## Appendix: Complete API Endpoint List

**Auth column key:**
- `No` — no token required
- `Yes` — requires `Authorization: Bearer <token>`
- `Yes+Sub` — requires token AND active subscription with `ai_analysis: true`
- `RL` — rate-limited per IP (see Warning 14 for limits)

| Method | Path | Auth | RL | Description |
|--------|------|------|----|-------------|
| GET | `/api/v1/auth/google/url` | No | — | Get Google OAuth URL |
| POST | `/api/v1/auth/google/callback` | No | ✓ | Google OAuth callback |
| POST | `/api/v1/auth/login` | No | ✓ | Email/password login (**form-encoded, not JSON**) |
| POST | `/api/v1/auth/logout` | Yes | — | Revoke token |
| POST | `/api/v1/auth/verify-otp` | No | ✓ | Verify email OTP |
| POST | `/api/v1/auth/resend-verification-otp` | No | ✓ | Resend OTP (3/min) |
| POST | `/api/v1/auth/forgot-password` | No | ✓ | Request password reset (3/min) |
| POST | `/api/v1/auth/verify-reset-code` | No | ✓ | Verify reset OTP |
| POST | `/api/v1/auth/reset-password` | No | ✓ | Set new password (**invalidates all tokens**) |
| GET | `/api/v1/auth/session-status` | Yes | — | Check session time remaining |
| POST | `/api/v1/auth/ping` | Yes | — | Keep session alive |
| POST | `/api/v1/users/register` | No | — | Register new user |
| GET | `/api/v1/profile/` | Yes | — | Get my profile |
| POST | `/api/v1/profile/questionnaire` | Yes | — | Submit questionnaire answers |
| GET | `/api/v1/profile/questionnaire` | Yes | — | Get saved questionnaire JSON |
| POST | `/api/v1/profile/complete` | Yes | — | Finalize onboarding (**then call `/ai/run`**) |
| POST | `/api/v1/profile/skip` | Yes | — | Skip questionnaire |
| POST | `/api/v1/profile/restart` | Yes | — | Reset questionnaire |
| GET | `/api/v1/profile/skills` | Yes | — | List skills |
| POST | `/api/v1/profile/skills` | Yes | — | Add a skill |
| DELETE | `/api/v1/profile/skills/{skill_id}` | Yes | — | Delete a skill |
| GET | `/api/v1/profile/skills/json` | Yes | — | Raw skills JSON |
| POST | `/api/v1/profile/skills/json` | Yes | — | Save raw skills JSON |
| GET | `/api/v1/profile/skills/search?q=` | Yes | — | Search predefined skills |
| GET | `/api/v1/profile/skill-categories` | Yes | — | List skill categories |
| GET | `/api/v1/ideas/` | Yes | — | List ideas (with filters) |
| POST | `/api/v1/ideas/` | Yes | — | Create idea |
| GET | `/api/v1/ideas/archived` | Yes | — | List archived ideas |
| PATCH | `/api/v1/ideas/{idea_id}/archive` | Yes | — | Archive idea |
| PATCH | `/api/v1/ideas/{idea_id}/unarchive` | Yes | — | Unarchive idea |
| GET | `/api/v1/billing/plans` | No | — | List all active subscription plans |
| POST | `/api/v1/billing/paypal/subscribe` | Yes | — | Create PayPal order for a plan |
| POST | `/api/v1/billing/paypal/capture` | Yes | — | Capture PayPal payment (activates subscription) |
| GET | `/api/v1/billing/subscription` | Yes | — | Get user's active subscription |
| DELETE | `/api/v1/billing/subscription` | Yes | — | Cancel active subscription |
| POST | `/api/v1/billing/paypal/webhook` | No | — | PayPal webhook (called by PayPal, not frontend) |
| POST | `/api/v1/billing/paymob/subscribe` | Yes | — | Initiate Paymob card payment — returns `iframe_url` |
| POST | `/api/v1/billing/paymob/webhook` | No | — | Paymob webhook — activates subscription on confirmed payment |
| GET | `/api/v1/groups` | Yes | — | List groups |
| POST | `/api/v1/groups` | Yes | — | Create group |
| PATCH | `/api/v1/groups/{group_id}` | Yes | — | Update group |
| DELETE | `/api/v1/groups/{group_id}` | Yes | — | Delete group |
| POST | `/api/v1/groups/{group_id}/invites` | Yes | — | Invite a user to group |
| POST | `/api/v1/groups/invites/accept` | Yes | — | Accept group invite |
| POST | `/api/v1/groups/{group_id}/join-requests` | Yes | — | Request to join a group |
| POST | `/api/v1/groups/join-requests/{id}/handle` | Yes | — | Approve or reject join request |
| GET | `/api/v1/groups/{group_id}/members` | Yes | — | List group members |
| PATCH | `/api/v1/groups/members/{member_id}` | Yes | — | Update member role |
| DELETE | `/api/v1/groups/members/{member_id}` | Yes | — | Remove member from group |
| GET | `/api/v1/groups/{group_id}/messages` | Yes | — | Get group messages |
| WS | `/api/v1/groups/{group_id}/ws?token=` | Yes | — | Real-time group chat (WebSocket) |
| GET | `/api/v1/notifications/` | Yes | — | Get notifications |
| GET | `/api/v1/export/` | Yes | — | List export jobs |
| POST | `/api/v1/export/` | Yes | — | Start data export |
| GET | `/api/v1/ai/health` | No | — | AI service health check (no subscription needed) |
| GET | `/api/v1/ai/version-check` | No | — | AI service version (no subscription needed) |
| POST | `/api/v1/ai/run` | Yes+Sub | — | Trigger AI pipeline (async — poll status) |
| GET | `/api/v1/ai/status` | Yes+Sub | — | Get pipeline status (**free — no quota**) |
| GET | `/api/v1/ai/idea` | Yes+Sub | — | Get generated idea text (**free — no quota**) |
| POST | `/api/v1/ai/chat` | Yes+Sub | — | Chat about idea (quota: yes) |
| POST | `/api/v1/ai/chat/stream` | Yes+Sub | — | Stream chat about idea (quota: yes) |
| POST | `/api/v1/ai/general-chat` | Yes+Sub | — | General AI assistant (quota: yes) |
| POST | `/api/v1/ai/general-chat/stream` | Yes+Sub | — | Stream general AI assistant (quota: yes) |
| POST | `/api/v1/ai/explain` | Yes+Sub | — | Explain a section (quota: yes) |
| POST | `/api/v1/ai/idea-intake` | Yes+Sub | — | Structure user's raw idea (quota: yes) |
| POST | `/api/v1/ai/idea-intake/run-problems` | Yes+Sub | — | Start problem discovery (async) |
| POST | `/api/v1/ai/idea-intake/start-chat` | Yes+Sub | — | Start idea chat — returning user flow |
| GET | `/api/v1/ai/idea-intake` | Yes+Sub | — | Get idea intake data (**free**) |
| GET | `/api/v1/ai/profile` | Yes+Sub | — | Get profile analysis (**free**) |
| GET | `/api/v1/ai/problems` | Yes+Sub | — | Get discovered problems (**free**) |
| GET | `/api/v1/ai/questionnaire` | Yes+Sub | — | Get questionnaire from AI (**free**) |
| POST | `/api/v1/ai/rerun/profile` | Yes+Sub | — | Re-run profile analysis (quota: yes) |
| POST | `/api/v1/ai/rerun/problems` | Yes+Sub | — | Re-run problem discovery (quota: yes) |
| POST | `/api/v1/ai/customers` | Yes+Sub | — | Generate customer analysis (quota: yes) |
| GET | `/api/v1/ai/customers` | Yes+Sub | — | Get customer analysis (**free**) |
| POST | `/api/v1/ai/customers/regenerate` | Yes+Sub | — | Regenerate (quota: yes) |
| POST | `/api/v1/ai/customers/regenerate-custom` | Yes+Sub | — | Regenerate with custom prompt (quota: yes) |
| POST | `/api/v1/ai/customers/chat` | Yes+Sub | — | Chat (quota: yes) |
| POST | `/api/v1/ai/customers/chat/stream` | Yes+Sub | — | Stream chat (quota: yes) |
| POST | `/api/v1/ai/competition` | Yes+Sub | — | Generate competition analysis (quota: yes) |
| GET | `/api/v1/ai/competition` | Yes+Sub | — | Get competition analysis (**free**) |
| POST | `/api/v1/ai/competition/regenerate` | Yes+Sub | — | Regenerate (quota: yes) |
| POST | `/api/v1/ai/competition/regenerate-custom` | Yes+Sub | — | Regenerate with custom prompt (quota: yes) |
| POST | `/api/v1/ai/competition/chat` | Yes+Sub | — | Chat (quota: yes) |
| POST | `/api/v1/ai/competition/chat/stream` | Yes+Sub | — | Stream chat (quota: yes) |
| POST | `/api/v1/ai/market-potential` | Yes+Sub | — | Generate market potential (quota: yes) |
| GET | `/api/v1/ai/market-potential` | Yes+Sub | — | Get market potential (**free**) |
| POST | `/api/v1/ai/market-potential/regenerate` | Yes+Sub | — | Regenerate (quota: yes) |
| POST | `/api/v1/ai/market-potential/regenerate-custom` | Yes+Sub | — | Custom regenerate (quota: yes) |
| POST | `/api/v1/ai/market-potential/chat` | Yes+Sub | — | Chat (quota: yes) |
| POST | `/api/v1/ai/market-potential/chat/stream` | Yes+Sub | — | Stream chat (quota: yes) |
| POST | `/api/v1/ai/idea-strategy` | Yes+Sub | — | Generate idea strategy (quota: yes) |
| GET | `/api/v1/ai/idea-strategy` | Yes+Sub | — | Get idea strategy (**free**) |
| POST | `/api/v1/ai/idea-strategy/regenerate` | Yes+Sub | — | Regenerate (quota: yes) |
| POST | `/api/v1/ai/idea-strategy/regenerate-custom` | Yes+Sub | — | Custom regenerate (quota: yes) |
| POST | `/api/v1/ai/idea-strategy/chat` | Yes+Sub | — | Chat (quota: yes) |
| POST | `/api/v1/ai/idea-strategy/chat/stream` | Yes+Sub | — | Stream chat (quota: yes) |
| POST | `/api/v1/ai/business-model` | Yes+Sub | — | Generate business model (quota: yes) |
| GET | `/api/v1/ai/business-model` | Yes+Sub | — | Get business model (**free**) |
| POST | `/api/v1/ai/business-model/regenerate` | Yes+Sub | — | Regenerate (quota: yes) |
| POST | `/api/v1/ai/business-model/regenerate-custom` | Yes+Sub | — | Custom regenerate (quota: yes) |
| POST | `/api/v1/ai/business-model/chat` | Yes+Sub | — | Chat (quota: yes) |
| POST | `/api/v1/ai/business-model/chat/stream` | Yes+Sub | — | Stream chat (quota: yes) |
| POST | `/api/v1/ai/functions-list` | Yes+Sub | — | Generate functions list (quota: yes) |
| GET | `/api/v1/ai/functions-list` | Yes+Sub | — | Get functions list (**free**) |
| POST | `/api/v1/ai/functions-list/regenerate` | Yes+Sub | — | Regenerate (quota: yes) |
| POST | `/api/v1/ai/functions-list/regenerate-custom` | Yes+Sub | — | Custom regenerate (quota: yes) |
| POST | `/api/v1/ai/functions-list/chat` | Yes+Sub | — | Chat (quota: yes) |
| POST | `/api/v1/ai/functions-list/chat/stream` | Yes+Sub | — | Stream chat (quota: yes) |
| POST | `/api/v1/ai/mvp-planning` | Yes+Sub | — | Generate MVP plan (quota: yes) |
| GET | `/api/v1/ai/mvp-planning` | Yes+Sub | — | Get MVP plan (**free**) |
| POST | `/api/v1/ai/mvp-planning/regenerate` | Yes+Sub | — | Regenerate (quota: yes) |
| POST | `/api/v1/ai/mvp-planning/regenerate-custom` | Yes+Sub | — | Custom regenerate (quota: yes) |
| POST | `/api/v1/ai/mvp-planning/chat` | Yes+Sub | — | Chat (quota: yes) |
| POST | `/api/v1/ai/mvp-planning/chat/stream` | Yes+Sub | — | Stream chat (quota: yes) |
| POST | `/api/v1/ai/unit-economics` | Yes+Sub | — | Generate unit economics (quota: yes) |
| GET | `/api/v1/ai/unit-economics` | Yes+Sub | — | Get unit economics (**free**) |
| POST | `/api/v1/ai/unit-economics/regenerate` | Yes+Sub | — | Regenerate (quota: yes) |
| POST | `/api/v1/ai/unit-economics/regenerate-custom` | Yes+Sub | — | Custom regenerate (quota: yes) |
| POST | `/api/v1/ai/unit-economics/chat` | Yes+Sub | — | Chat (quota: yes) |
| POST | `/api/v1/ai/unit-economics/chat/stream` | Yes+Sub | — | Stream chat (quota: yes) |
| POST | `/api/v1/ai/go-to-market` | Yes+Sub | — | Generate GTM plan (quota: yes) |
| GET | `/api/v1/ai/go-to-market` | Yes+Sub | — | Get GTM plan (**free**) |
| POST | `/api/v1/ai/go-to-market/regenerate` | Yes+Sub | — | Regenerate (quota: yes) |
| POST | `/api/v1/ai/go-to-market/regenerate-custom` | Yes+Sub | — | Custom regenerate (quota: yes) |
| POST | `/api/v1/ai/go-to-market/chat` | Yes+Sub | — | Chat (quota: yes) |
| POST | `/api/v1/ai/go-to-market/chat/stream` | Yes+Sub | — | Stream chat (quota: yes) |

---

*This document was generated from the actual source code of Bizify-Backend and bizifyAI.*
*Last updated: 2026-05-18 — see Changelog at the top for all post-initial changes.*
