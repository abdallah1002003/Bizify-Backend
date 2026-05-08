# Bizify Backend — Technical Documentation

Welcome to the **Bizify Backend**! This is a FastAPI backend for an AI-assisted business strategy platform. It supports entrepreneurs from account creation through onboarding, skill capture, idea creation, AI analysis, team collaboration, partner discovery, subscription billing, document import, export jobs, notifications, and administrative review.

> **Version:** `0.1.0` — For the full change history, see [CHANGELOG.md](docs/CHANGELOG.md).

To keep documentation modular and easy to read, the system's technical details are organized into dedicated documents.

## Table of Contents

### 1. [Overview & Architecture](docs/ARCHITECTURE.md)
* System overview and user personas.
* Runtime component architecture diagram.
* Request lifecycle and layer responsibilities.

### 2. [Database Schema](docs/DATABASE_SCHEMA.md)
* Complete Entity-Relationship definitions.
* Domains: Core User Management, Ideas & Businesses, Collaboration, Skills & Partners, Roadmap & Guidance, Billing, and System Logs.

### 3. [CRUD Operations Reference](docs/CRUD_OPERATIONS.md)
* SQLAlchemy base repository definitions.
* Detailed operations for Users, Profiles, Ideas, Groups, Skills, Partners, Billing, Notifications, and Guidance.

### 4. [Database Connections](docs/DATABASE_CONNECTION.md)
* PostgreSQL configuration and session lifecycle (`get_db()`).
* Local SQLite compatibility hooks.
* Redis caching and Alembic migration workflows.

### 5. [Tech Stack](docs/TECH_STACK.md)
* Core frameworks: FastAPI, Uvicorn, Pydantic.
* Libraries for authentication, background tasks (Celery), and file processing (`pypdf`, `python-docx`, etc.).

### 6. [API Surface](docs/API_DOCUMENTATION.md)
* Detailed REST endpoint documentation and JSON payloads.
* Covers Auth, Users, Profiling, Ideas, Groups, Notifications, Billing, Export/Import, and Admin routes.

### 7. [Security & Access Control](docs/SECURITY.md)
* JWT authentication, password hashing, and token revocation.
* Role-Based Access Control (RBAC), IDOR protection, and audit logging.

### 8. [Background & Real-time Flows](docs/BACKGROUND_REALTIME.md)
* Sequence diagrams for Celery export jobs.
* Group chat WebSocket workflows.
* Notification Server-Sent Events (SSE).
* External AI pipeline polling mechanisms.

### 9. [External Integrations](docs/INTEGRATIONS.md)
* Google OAuth2, SMTP Email, and Redis.
* Payment Gateways: PayPal Orders API and Paymob iframe checkouts.
* Supabase Storage and External AI connectivity.

### 10. [Configuration & Setup](docs/SETUP_CONFIGURATION.md)
* Environment variables configuration (`.env`).
* Local environment setup (`uv` / `pip`).
* Running migrations, data seeders, and starting the `uvicorn` server.

### 11. [Error Handling & Standard Responses](docs/ERROR_HANDLING.md)
* Standard HTTP status codes mapping to business logic.
* Standardized JSON exception responses.
* Validation error payload structure (422 Unprocessable Entity).

### 12. [Deployment Guide](docs/DEPLOYMENT.md)
* Production architecture recommendations.
* Dockerfile and Docker Compose configurations for App, Redis, and Celery.
* Nginx reverse proxy configuration for API and WebSockets.
* Production Readiness Checklist: what's safe to document vs. what must stay secret.

### 13. [Changelog](docs/CHANGELOG.md)
* Version history starting from `0.1.0`.
* Full list of implemented features in the initial release.
* Planned features for future versions (rate limiting, tests, email queue).

### 14. [Postman Collection](docs/Bizify_API.postman_collection.json)
* Ready-to-import Postman collection covering all 13 API domains.
* Includes collection variables for `base_url` and `token`.
* Import into Postman: **File → Import → select `Bizify_API.postman_collection.json`**.

---

> **Note:** For quick development starts, refer to **Section 10 (Configuration & Setup)** to get the server running locally.
