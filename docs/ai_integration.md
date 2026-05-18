# 🤖 AI Pipeline — Frontend Integration Guide

> **Last Updated:** 2026-05-18 | **Latest Commit:** `30b591c` (main branch)

---

## 📁 Key Source Files

| Purpose | Path |
|---------|------|
| All AI Endpoints (75+ routes) | `app/api/v1/ai_pipeline.py` |
| Service layer (calls external AI) | `app/services/ai_pipeline_service.py` |
| Request / Response Schemas | `app/schemas/ai_pipeline.py` |
| Rate-limiting dependency | `app/api/dependencies.py` → `check_ai_usage` |

> **Note for AI assistants (Cursor / Copilot):** These tools only index files that are open in the editor. If your assistant reports "no integration found," open `app/api/v1/ai_pipeline.py` manually and it will detect all routes.

---

## 🌐 Base URL

```
http://localhost:8000/api/v1/ai
```

---

## 🔐 Authentication

Every AI endpoint requires a **Bearer Token** in the request header:

```http
Authorization: Bearer <access_token>
```

Obtain a token via: `POST /api/v1/auth/login`

---

## 📋 Endpoint Reference

### 🔧 System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/run` | Trigger the AI pipeline for the authenticated user |
| `GET` | `/ai/status` | Get the current pipeline status |
| `GET` | `/ai/health` | Health check |
| `GET` | `/ai/version-check` | Version check |

---

### 👤 Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ai/profile` | Retrieve the generated profile analysis |
| `GET` | `/ai/questionnaire` | Fetch the onboarding questionnaire |
| `POST` | `/ai/rerun/profile` | Re-run the profile analysis |

---

### 🚨 Problems

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ai/problems` | Retrieve the generated problems analysis |
| `POST` | `/ai/rerun/problems` | Re-run the problems analysis |

---

### 💡 Idea

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ai/idea` | Retrieve the generated idea |
| `POST` | `/ai/idea-intake` | Submit a new idea for analysis |
| `GET` | `/ai/idea-intake` | Retrieve the submitted idea |
| `POST` | `/ai/idea-intake/start-chat` | Start a chat session about the idea |
| `POST` | `/ai/idea-intake/run-problems` | Run problems analysis for the idea |

---

### 👥 Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/customers` | Generate customer analysis |
| `GET` | `/ai/customers` | Retrieve customer analysis |
| `POST` | `/ai/customers/regenerate` | Regenerate customer analysis |
| `POST` | `/ai/customers/regenerate-custom` | Regenerate with a custom prompt |
| `POST` | `/ai/customers/chat` | Chat about customer analysis |
| `POST` | `/ai/customers/chat/stream` | Streaming chat (SSE) |

---

### 🏆 Competition

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/competition` | Generate competition analysis |
| `GET` | `/ai/competition` | Retrieve competition analysis |
| `POST` | `/ai/competition/regenerate` | Regenerate competition analysis |
| `POST` | `/ai/competition/regenerate-custom` | Regenerate with a custom prompt |
| `POST` | `/ai/competition/chat` | Chat about competition analysis |
| `POST` | `/ai/competition/chat/stream` | Streaming chat (SSE) |

---

### 📈 Market Potential

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/market-potential` | Generate market potential analysis |
| `GET` | `/ai/market-potential` | Retrieve market potential analysis |
| `POST` | `/ai/market-potential/regenerate` | Regenerate analysis |
| `POST` | `/ai/market-potential/regenerate-custom` | Regenerate with a custom prompt |
| `POST` | `/ai/market-potential/chat` | Chat about market potential |
| `POST` | `/ai/market-potential/chat/stream` | Streaming chat (SSE) |

---

### 💡 Idea Strategy

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/idea-strategy` | Generate idea strategy |
| `GET` | `/ai/idea-strategy` | Retrieve idea strategy |
| `POST` | `/ai/idea-strategy/regenerate` | Regenerate strategy |
| `POST` | `/ai/idea-strategy/regenerate-custom` | Regenerate with a custom prompt |
| `POST` | `/ai/idea-strategy/chat` | Chat about idea strategy |
| `POST` | `/ai/idea-strategy/chat/stream` | Streaming chat (SSE) |

---

### 💼 Business Model

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/business-model` | Generate business model |
| `GET` | `/ai/business-model` | Retrieve business model |
| `POST` | `/ai/business-model/regenerate` | Regenerate business model |
| `POST` | `/ai/business-model/regenerate-custom` | Regenerate with a custom prompt |
| `POST` | `/ai/business-model/chat` | Chat about business model |
| `POST` | `/ai/business-model/chat/stream` | Streaming chat (SSE) |

---

### ⚙️ Functions List

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/functions-list` | Generate functions list |
| `GET` | `/ai/functions-list` | Retrieve functions list |
| `POST` | `/ai/functions-list/regenerate` | Regenerate functions list |
| `POST` | `/ai/functions-list/regenerate-custom` | Regenerate with a custom prompt |
| `POST` | `/ai/functions-list/chat` | Chat about functions list |
| `POST` | `/ai/functions-list/chat/stream` | Streaming chat (SSE) |

---

### 🗺️ MVP Planning

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/mvp-planning` | Generate MVP plan |
| `GET` | `/ai/mvp-planning` | Retrieve MVP plan |
| `POST` | `/ai/mvp-planning/regenerate` | Regenerate MVP plan |
| `POST` | `/ai/mvp-planning/regenerate-custom` | Regenerate with a custom prompt |
| `POST` | `/ai/mvp-planning/chat` | Chat about MVP plan |
| `POST` | `/ai/mvp-planning/chat/stream` | Streaming chat (SSE) |

---

### 💰 Unit Economics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/unit-economics` | Generate unit economics analysis |
| `GET` | `/ai/unit-economics` | Retrieve unit economics analysis |
| `POST` | `/ai/unit-economics/regenerate` | Regenerate analysis |
| `POST` | `/ai/unit-economics/regenerate-custom` | Regenerate with a custom prompt |
| `POST` | `/ai/unit-economics/chat` | Chat about unit economics |
| `POST` | `/ai/unit-economics/chat/stream` | Streaming chat (SSE) |

---

### 🚀 Go-To-Market

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/go-to-market` | Generate go-to-market strategy |
| `GET` | `/ai/go-to-market` | Retrieve go-to-market strategy |
| `POST` | `/ai/go-to-market/regenerate` | Regenerate strategy |
| `POST` | `/ai/go-to-market/regenerate-custom` | Regenerate with a custom prompt |
| `POST` | `/ai/go-to-market/chat` | Chat about go-to-market strategy |
| `POST` | `/ai/go-to-market/chat/stream` | Streaming chat (SSE) |

---

### 💬 Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/chat` | Core AI chatbot |
| `POST` | `/ai/chat/stream` | Core AI chatbot (SSE streaming) |
| `POST` | `/ai/general-chat` | General-purpose chatbot |
| `POST` | `/ai/general-chat/stream` | General chatbot (SSE streaming) |
| `POST` | `/ai/explain` | Ask the AI to explain any content |

---

## 🔒 Rate Limiting & Plan Protection

Every AI endpoint is automatically protected by the `check_ai_usage` dependency:

| Condition | Response |
|-----------|----------|
| Plan has `"ai_analysis": false` | `403 Forbidden` — upgrade required |
| Request quota exhausted | `429 Too Many Requests` |
| Within quota | Request allowed + counter incremented |

The quota limit is read dynamically from the user's active subscription plan (`features_json → ai_requests`), defaulting to **100 requests** for users with no active plan.

---

## 🖥️ Interactive API Docs (Swagger UI)

```
http://localhost:8000/docs
```

Look for sections prefixed with **`AI -`** (e.g., `AI - Customers`, `AI - Business Model`, etc.)

---

## 🔄 Quick Start for Frontend

```bash
# 1. Pull the latest changes
git pull origin main

# 2. Start the backend
uv run python -m app.main

# 3. Open Swagger UI
open http://localhost:8000/docs
```

1. Login via `POST /api/v1/auth/login` and copy the `access_token`.
2. Click **Authorize 🔒** at the top of the Swagger page and paste the token.
3. Navigate to any `AI -` section and click **Try it out → Execute**.
