# Bizify — Tech Stack & System Tools

A comprehensive reference for all tools, libraries, and external services used in the Bizify backend.

---

## 1. Core Framework

| Tool | Version | Purpose |
|---|---|---|
| **Python** | ≥ 3.9 | Primary backend language |
| **FastAPI** | Latest | REST API framework — async, high performance |
| **Uvicorn** | Standard | ASGI server for running FastAPI |
| **Pydantic v2** | Latest | Data validation and settings management |
| **pydantic-settings** | Latest | Loading settings from `.env` files |

---

## 2. Database

| Tool | Version | Purpose |
|---|---|---|
| **PostgreSQL** | — | Primary relational database |
| **SQLAlchemy** | Latest | ORM — defining models and executing queries |
| **Alembic** | Latest | Database migration management |
| **psycopg2-binary** | ≥ 2.9.11 | PostgreSQL driver for Python |

> **Note:** UUIDs are used as primary keys across all tables (via `sqlalchemy.dialects.postgresql.UUID`).

---

## 3. Authentication & Security

| Tool | Purpose |
|---|---|
| **python-jose[cryptography]** | JWT token generation and verification |
| **PyJWT** | Supplementary JWT handling |
| **passlib[bcrypt]** | Password hashing |
| **bcrypt < 4.0.0** | Pinned bcrypt version for passlib compatibility |
| **Google OAuth** (`google_client.py`) | Social login via Google — validates ID tokens from the frontend |
| **Token Blacklist** (`token_blacklist` table) | Revoked JWT tracking on logout |
| **python-multipart** | Parsing `multipart/form-data` for file uploads |

**Auth Flow:**
- JWT HS256 tokens, expire in 7 days (`ACCESS_TOKEN_EXPIRE_MINUTES=10080`)
- Account lockout after failed login attempts (`failed_login_attempts`, `locked_until`)
- OTP-based verification for email confirmation and password reset (`account_verifications`)

---

## 4. Caching

| Tool | Version | Purpose |
|---|---|---|
| **Redis** | ≥ 7.0.1 | In-memory cache and Celery message broker |

**Usage (`cache.py`):**
- Caching frequently accessed data (e.g., skill lists, guidance stages)
- Acts as Celery broker and result backend (`redis://localhost:6379/0`)

---

## 5. Background Tasks

| Tool | Version | Purpose |
|---|---|---|
| **Celery** | ≥ 5.6.2 | Distributed task queue for async background jobs |
| **Redis** | ≥ 7.0.1 | Celery broker & result backend |

**Tasks:**
- Data export jobs (`export_service`) — routed to `export_queue`
- Auto-discovery of tasks across `app.services`

---

## 6. Real-Time Communication

| Tool | Purpose |
|---|---|
| **FastAPI WebSockets** | Real-time bidirectional communication |
| **GroupConnectionManager** (`sockets/group_manager.py`) | In-memory WebSocket connection pool per group — broadcasts messages to all connected members |

---

## 7. File Handling & Document Processing

| Tool | Version | Purpose |
|---|---|---|
| **pypdf** | ≥ 6.9.1 | Extracting text from PDF files |
| **python-docx** | ≥ 1.2.0 | Extracting text from Word documents (`.docx`) |
| **python-pptx** | ≥ 1.0.2 | Extracting text from PowerPoint files (`.pptx`) |
| **fpdf2** | ≥ 2.8.4 | Generating PDF reports |
| **ImageKit** (`imagekitio`) | ≥ 5.2.0 | Cloud image storage and optimization |
| **Supabase Storage** | ≥ 2.12.0 | Storing partner documents (bucket: `partner-documents`) |

---

## 8. Payment Gateways

| Tool | Purpose |
|---|---|
| **PayPal** (`paypal_client.py`) | International payments — orders, captures, and webhooks. Supports `sandbox` and `live` modes |
| **Paymob** (`paymob_client.py`) | Local Egyptian payments — Visa/Mastercard via iframe integration |

**Stored Identifiers:**
- PayPal: `paypal_order_id`, `paypal_capture_id`, `paypal_subscription_id`
- Paymob: `paymob_order_id`, `paymob_transaction_id`

---

## 9. Email

| Tool | Purpose |
|---|---|
| **Gmail SMTP** | Sending transactional emails (verification, password reset, notifications) |
| **smtplib / MIME** (`mail.py`) | Python standard email composition and TLS delivery on port 587 |

---

## 10. HTTP Clients

| Tool | Version | Purpose |
|---|---|---|
| **httpx** | ≥ 0.27.0 | Async HTTP client — used for Google OAuth token verification and external API calls |
| **requests** | ≥ 2.32.5 | Synchronous HTTP client — used for PayPal and Paymob REST API calls |

---

## 11. Development & Quality Tools

| Tool | Purpose |
|---|---|
| **Ruff** | Linter and import sorter (`E`, `F`, `I`, `B`, `C4`, `UP` rules, line-length 88) |
| **pytest** | Unit and integration testing (`tests/` directory) |
| **uv** | Fast Python package manager (`uv.lock`) |
| **Alembic** | Database migrations (`alembic/versions/`) |

---

## 12. Architecture Overview

```
Client (HTTP / WebSocket)
        │
        ▼
  FastAPI (Uvicorn)
        │
        ├── REST API (/api/v1/*)
        │       ├── Auth (JWT + Google OAuth)
        │       ├── Ideas / Businesses / Roadmap
        │       ├── Groups + Invites + Requests
        │       ├── AI Chat Sessions
        │       ├── Partner Profiles + Requests
        │       └── Billing (PayPal / Paymob)
        │
        ├── WebSocket (/ws/groups/{group_id})
        │       └── GroupConnectionManager (in-memory)
        │
        ├── Background (Celery + Redis)
        │       └── Export Jobs
        │
        └── Data Layer
                ├── PostgreSQL (via SQLAlchemy + Alembic)
                ├── Redis (Cache + Celery Broker)
                ├── Supabase Storage (Partner Docs)
                └── ImageKit (Images)
```
