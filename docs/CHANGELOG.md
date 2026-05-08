# Bizify — Changelog

All notable changes to this project are documented here.

This project adheres to [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — Initial Release

**Status:** Development / Pre-production

### Added
- FastAPI application factory with CORS middleware and versioned router (`/api/v1`).
- Full JWT authentication system with login, logout, OTP verification, password reset, session timeout, and token blacklisting.
- Google OAuth2 login and registration flow.
- Brute-force login protection (5 failed attempts → 15-minute lockout).
- Role-Based Access Control (RBAC) with `ADMIN`, `USER`, `ENTREPRENEUR`, `MENTOR`, `SUPPLIER`, `MANUFACTURER` roles.
- Entrepreneur user registration, onboarding questionnaire, profile management, and skill gap tracking.
- Partner registration (Mentor, Supplier, Manufacturer) with multi-document upload and admin approval workflow.
- Business idea CRUD with AI scoring, budget, feasibility, archival, and filtering.
- Group collaboration with invite system, join requests, member role management, and WebSocket real-time chat.
- Server-Sent Events (SSE) notification stream with preferences and bulk-status management.
- Business Guidance system with structured stages, concepts, and user progress tracking.
- User Settings with password change (global logout), notification preferences, privacy settings, and account deletion.
- Subscription billing with dual payment gateway support: **PayPal Orders API** (international) and **Paymob iframe** (Egypt local card payments), including signed webhook verification.
- Asynchronous data export pipeline using Celery and Redis: supports JSON, PDF, and DOCX formats.
- Document import with text extraction from PDF, Word, and PowerPoint files.
- AI Pipeline integration: collects user profile data, sends to external AI engine, polls for status, and stores results in `personalization_profile`.
- Admin dashboard: user search, promote, suspend, delete; partner approval/rejection; security log viewing; statistics endpoint.
- Alembic migration environment for schema evolution.
- SQLite compatibility mode for zero-config local development.
- Seed scripts for plans (`scripts/seed_plans.py`), predefined skills (`scripts/seed_skills.py`), guidance content, and demo data.
- Basic smoke check script using FastAPI `TestClient`.
- Supabase Storage integration for partner documents.
- Redis-backed cache service (`CacheService`) with TTL and JSON serialization.

---

## [Planned — Future Releases]

The following items are planned for future versions and are **not yet implemented**:

| Feature | Notes |
|---|---|
| **Rate Limiting** | No rate limiting is currently applied to any endpoint. Planned implementation via `slowapi`. |
| **Unit & Integration Tests** | The `tests/` directory exists but is empty. Test coverage is planned using `pytest` with a dedicated SQLite test database. |
| **Email Queue** | Emails are currently sent synchronously within the request. A dedicated Celery email queue is planned for reliability. |
| **Admin Audit Log UI** | Admin action logs are stored in the database but no dedicated UI or filter endpoint exists. |
