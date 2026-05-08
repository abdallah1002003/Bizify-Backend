# Bizify — Comprehensive Automation Testing Plan
> **Version:** 3.0 | **Date:** 2026-05-08 | **Framework:** `pytest` + FastAPI `TestClient`

---

## 🗂️ Overview

The goal of this document is to define **every single test case** for the Bizify backend project. 
This plan covers all 13 API modules and ensures that no endpoint is left behind.

For each test, we define:
- **Test Objective** (What endpoint or scenario is being tested).
- **Method & Endpoint** (How it will be tested).
- **Priority** (🔴 Critical / 🟡 Important / 🟢 Nice-to-have).
- **Status** (⬜ Pending / ✅ Done / ❌ Failed).

---

## ⚙️ Test Environment Setup

### Required Tools

| Tool | Purpose | Note |
|---|---|---|
| `pytest` | Test execution framework | The core testing library |
| `httpx` | HTTP request mocking | Required for FastAPI's `TestClient` |
| `pytest-asyncio` | Async test support | Necessary for WebSockets and SSE |
| `pytest-cov` | Coverage reporting | To track tested vs untested code |
| `Faker` | Mock data generation | For random emails, names, etc. |

### Installation Command
```bash
pip install pytest httpx pytest-asyncio pytest-cov faker
```

### Test Directory Structure
```
tests/
├── conftest.py           # Shared settings, mock DB, and fixtures
├── test_health.py        # Health check endpoints
├── test_auth.py          # Authentication (Login, Register, OTP, Google)
├── test_users.py         # User & Partner Registration and Profiles
├── test_profile.py       # Onboarding Questionnaire & Skills
├── test_ideas.py         # Business Ideas Management
├── test_groups.py        # Teams, Invites, WebSockets
├── test_notifications.py # Notifications & SSE
├── test_billing.py       # Subscriptions (PayPal & Paymob)
├── test_admin.py         # Admin Dashboard & User Management
├── test_export.py        # Data Export Jobs
├── test_import.py        # Document Uploads & AI parsing
├── test_guidance.py      # Business Guidance & Progress
├── test_settings.py      # Account Settings & Deactivation
└── test_ai_pipeline.py   # AI Analysis Pipeline
```

### Database Strategy
- **Isolated Database:** A temporary database (e.g., SQLite in-memory `sqlite:///:memory:`) is created before each test session and destroyed afterward to prevent polluting real development data.
- **External Mocking:** Services like SMTP (Emails), Stripe/PayPal/Paymob (Billing), and External AI Pipelines are **Mocked** so tests run fast and don't hit external rate limits.

---

## 📋 Detailed Test Cases (Endpoint by Endpoint)

---

### 1. 🏥 Health Check (`test_health.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| H-01 | Root endpoint returns greeting | GET | `/` | 200 | 🔴 Critical | ⬜ |
| H-02 | Health check returns healthy status | GET | `/health` | 200 | 🔴 Critical | ⬜ |

---

### 2. 🔐 Authentication (`test_auth.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| A-01 | Get Google Auth URL | GET | `/api/v1/auth/google/url` | 200 | 🟡 Important | ⬜ |
| A-02 | Exchange Google code for token | POST | `/api/v1/auth/google/callback` | 200 | 🔴 Critical | ⬜ |
| A-03 | Login with valid credentials returns JWT | POST | `/api/v1/auth/login` | 200 | 🔴 Critical | ⬜ |
| A-04 | Login with invalid credentials fails | POST | `/api/v1/auth/login` | 401 | 🔴 Critical | ⬜ |
| A-05 | Logout invalidates token | POST | `/api/v1/auth/logout` | 200 | 🔴 Critical | ⬜ |
| A-06 | Verify account via OTP | POST | `/api/v1/auth/verify-otp` | 200 | 🔴 Critical | ⬜ |
| A-07 | Resend verification OTP | POST | `/api/v1/auth/resend-verification-otp` | 200 | 🟡 Important | ⬜ |
| A-08 | Request password reset (Forgot Password) | POST | `/api/v1/auth/forgot-password` | 200 | 🟡 Important | ⬜ |
| A-09 | Reset password using valid OTP | POST | `/api/v1/auth/reset-password` | 200 | 🔴 Critical | ⬜ |
| A-10 | Get current session status | GET | `/api/v1/auth/session-status` | 200 | 🟡 Important | ⬜ |
| A-11 | Keep session alive (Ping) | POST | `/api/v1/auth/ping` | 200 | 🟡 Important | ⬜ |

---

### 3. 👤 Users & Partner Registration (`test_users.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| U-01 | Register basic entrepreneur account | POST | `/api/v1/users/register` | 201 | 🔴 Critical | ⬜ |
| U-02 | Register partner account with files | POST | `/api/v1/users/register-partner` | 201 | 🔴 Critical | ⬜ |
| U-03 | Update base user profile | POST | `/api/v1/users/profile` | 200 | 🟡 Important | ⬜ |
| U-04 | Create secondary partner profile | POST | `/api/v1/users/partner-profile` | 200 | 🟡 Important | ⬜ |
| U-05 | Update existing partner profile | PATCH | `/api/v1/users/partner-profile` | 200 | 🟡 Important | ⬜ |
| U-06 | Fetch user's partner profile | GET | `/api/v1/users/partner-profile` | 200 | 🟡 Important | ⬜ |

---

### 4. 🧭 User Profile, Onboarding & Skills (`test_profile.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| P-01 | Submit onboarding questionnaire | POST | `/api/v1/profile/questionnaire` | 200 | 🔴 Critical | ⬜ |
| P-02 | Skip onboarding questionnaire | POST | `/api/v1/profile/skip` | 200 | 🟡 Important | ⬜ |
| P-03 | Skip beginner guide | POST | `/api/v1/profile/skip-guide` | 200 | 🟡 Important | ⬜ |
| P-04 | Restart questionnaire | POST | `/api/v1/profile/restart` | 200 | 🟡 Important | ⬜ |
| P-05 | Finalize onboarding status | POST | `/api/v1/profile/complete` | 200 | 🔴 Critical | ⬜ |
| P-06 | Update guide tutorial status | PATCH | `/api/v1/profile/guide-status` | 200 | 🟢 Nice | ⬜ |
| P-07 | Fetch full user profile | GET | `/api/v1/profile/` | 200 | 🔴 Critical | ⬜ |
| P-08 | List skill categories | GET | `/api/v1/profile/skill-categories` | 200 | 🟡 Important | ⬜ |
| P-09 | Search predefined skills | GET | `/api/v1/profile/skills/search` | 200 | 🟡 Important | ⬜ |
| P-10 | Fetch user's selected skills | GET | `/api/v1/profile/skills` | 200 | 🔴 Critical | ⬜ |
| P-11 | Add skill to user profile | POST | `/api/v1/profile/skills` | 201 | 🔴 Critical | ⬜ |
| P-12 | Delete skill from user profile | DELETE | `/api/v1/profile/skills/{id}` | 204 | 🟡 Important | ⬜ |

---

### 5. 💡 Ideas (`test_ideas.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| I-01 | Create new business idea | POST | `/api/v1/ideas/` | 201 | 🔴 Critical | ⬜ |
| I-02 | Fetch list of user ideas | GET | `/api/v1/ideas/` | 200 | 🔴 Critical | ⬜ |
| I-03 | Archive an idea | PATCH | `/api/v1/ideas/{id}/archive` | 200 | 🟡 Important | ⬜ |
| I-04 | Fetch archived ideas | GET | `/api/v1/ideas/archived` | 200 | 🟡 Important | ⬜ |
| I-05 | Unarchive an idea | PATCH | `/api/v1/ideas/{id}/unarchive` | 200 | 🟡 Important | ⬜ |

---

### 6. 👥 Groups & Collaboration (`test_groups.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| G-01 | Create a new group | POST | `/api/v1/groups` | 200 | 🔴 Critical | ⬜ |
| G-02 | Get list of user's groups | GET | `/api/v1/groups` | 200 | 🔴 Critical | ⬜ |
| G-03 | Update group details | PATCH | `/api/v1/groups/{id}` | 200 | 🟡 Important | ⬜ |
| G-04 | Delete a group | DELETE | `/api/v1/groups/{id}` | 200 | 🟡 Important | ⬜ |
| G-05 | Invite member to group | POST | `/api/v1/groups/{id}/invites` | 200 | 🟡 Important | ⬜ |
| G-06 | Accept group invite via token | POST | `/api/v1/groups/invites/accept` | 200 | 🔴 Critical | ⬜ |
| G-07 | Send join request to group | POST | `/api/v1/groups/{id}/join-requests`| 200 | 🟡 Important | ⬜ |
| G-08 | Admin handles join request | POST | `/api/v1/groups/join-requests/...`| 200 | 🟡 Important | ⬜ |
| G-09 | Fetch group members | GET | `/api/v1/groups/{id}/members` | 200 | 🔴 Critical | ⬜ |
| G-10 | Update member role/access | PATCH | `/api/v1/groups/members/{id}` | 200 | 🟡 Important | ⬜ |
| G-11 | Remove member from group | DELETE | `/api/v1/groups/members/{id}` | 200 | 🟡 Important | ⬜ |
| G-12 | Fetch group chat messages | GET | `/api/v1/groups/{id}/messages`| 200 | 🔴 Critical | ⬜ |
| G-13 | Send group chat message | POST | `/api/v1/groups/{id}/messages`| 201 | 🔴 Critical | ⬜ |
| G-14 | Connect to Group WebSocket | WS | `/api/v1/groups/{id}/ws` | 101 | 🔴 Critical | ⬜ |

---

### 7. 🔔 Notifications (`test_notifications.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| N-01 | List user notifications | GET | `/api/v1/notifications/` | 200 | 🔴 Critical | ⬜ |
| N-02 | Connect to SSE stream | GET | `/api/v1/notifications/stream` | 200 | 🔴 Critical | ⬜ |
| N-03 | Update single notification status | PATCH | `/api/v1/notifications/{id}/status`| 200 | 🟡 Important | ⬜ |
| N-04 | Bulk update notifications status | PATCH | `/api/v1/notifications/status/bulk`| 200 | 🟡 Important | ⬜ |
| N-05 | Fetch notification settings | GET | `/api/v1/notifications/settings` | 200 | 🟢 Nice | ⬜ |
| N-06 | Update notification settings | PATCH | `/api/v1/notifications/settings` | 200 | 🟢 Nice | ⬜ |
| N-07 | Admin triggers maintenance | POST | `/api/v1/notifications/maintenance`| 204 | 🟢 Nice | ⬜ |
| N-08 | Send test notification | POST | `/api/v1/notifications/test-notify`| 201 | 🟡 Important | ⬜ |
| N-09 | Delete single notification | DELETE | `/api/v1/notifications/{id}` | 204 | 🟡 Important | ⬜ |
| N-10 | Bulk delete notifications | POST | `/api/v1/notifications/bulk-delete`| 200 | 🟡 Important | ⬜ |
| N-11 | Delete all notifications | DELETE | `/api/v1/notifications/status/all`| 200 | 🟡 Important | ⬜ |

---

### 8. 💳 Billing & Subscriptions (`test_billing.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| B-01 | List all active billing plans | GET | `/api/v1/billing/plans` | 200 | 🔴 Critical | ⬜ |
| B-02 | Create PayPal order | POST | `/api/v1/billing/paypal/subscribe` | 200 | 🔴 Critical | ⬜ |
| B-03 | Capture PayPal payment | POST | `/api/v1/billing/paypal/capture` | 200 | 🔴 Critical | ⬜ |
| B-04 | Get current subscription details | GET | `/api/v1/billing/subscription` | 200 | 🔴 Critical | ⬜ |
| B-05 | Cancel current subscription | DELETE | `/api/v1/billing/subscription` | 200 | 🟡 Important | ⬜ |
| B-06 | Handle PayPal Webhook | POST | `/api/v1/billing/paypal/webhook` | 200 | 🔴 Critical | ⬜ |
| B-07 | Create Paymob order | POST | `/api/v1/billing/paymob/subscribe` | 200 | 🔴 Critical | ⬜ |
| B-08 | Handle Paymob Webhook | POST | `/api/v1/billing/paymob/webhook` | 200 | 🔴 Critical | ⬜ |

---

### 9. 🛡️ Admin Dashboard (`test_admin.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| AD-01 | List partner role requests | GET | `/api/v1/admin/requests` | 200 | 🟡 Important | ⬜ |
| AD-02 | Search user by email | GET | `/api/v1/admin/users/search` | 200 | 🟡 Important | ⬜ |
| AD-03 | Delete user by email | DELETE | `/api/v1/admin/users` | 204 | 🔴 Critical | ⬜ |
| AD-04 | Approve partner request | PATCH | `/api/v1/admin/approve/{id}` | 200 | 🔴 Critical | ⬜ |
| AD-05 | Reject partner request | PATCH | `/api/v1/admin/reject/{id}` | 200 | 🔴 Critical | ⬜ |
| AD-06 | View security logs | GET | `/api/v1/admin/security-logs` | 200 | 🟢 Nice | ⬜ |
| AD-07 | Promote user to new role | PATCH | `/api/v1/admin/users/{id}/promote` | 200 | 🔴 Critical | ⬜ |
| AD-08 | List all users (Paginated) | GET | `/api/v1/admin/users` | 200 | 🔴 Critical | ⬜ |
| AD-09 | Get admin dashboard stats | GET | `/api/v1/admin/stats` | 200 | 🟡 Important | ⬜ |
| AD-10 | Suspend user account | PATCH | `/api/v1/admin/users/{id}/suspend` | 200 | 🔴 Critical | ⬜ |

---

### 10. 📤 Export (`test_export.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| EX-01 | Request new data export job | POST | `/api/v1/export/` | 200 | 🔴 Critical | ⬜ |
| EX-02 | Cancel running export job | POST | `/api/v1/export/{id}/cancel` | 200 | 🟡 Important | ⬜ |
| EX-03 | Get export job status | GET | `/api/v1/export/{id}` | 200 | 🟡 Important | ⬜ |
| EX-04 | Download exported file | GET | `/api/v1/export/{id}/download` | 200 | 🔴 Critical | ⬜ |

---

### 11. 📥 Import (`test_import.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| IM-01 | Upload document & extract text | POST | `/api/v1/import/upload` | 200 | 🔴 Critical | ⬜ |
| IM-02 | Delete imported document | DELETE | `/api/v1/import/{id}` | 200 | 🟡 Important | ⬜ |
| IM-03 | Export document for AI Pipeline| GET | `/api/v1/import/{id}/export-ai` | 200 | 🟡 Important | ⬜ |

---

### 12. 🧩 Business Guidance (`test_guidance.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| GD-01 | List all guidance stages | GET | `/api/v1/guidance/stages` | 200 | 🔴 Critical | ⬜ |
| GD-02 | List concepts for a stage | GET | `/api/v1/guidance/stages/{id}/concepts` | 200 | 🟡 Important | ⬜ |
| GD-03 | View concept details | GET | `/api/v1/guidance/concepts/{id}` | 200 | 🟡 Important | ⬜ |
| GD-04 | Update user progress | POST | `/api/v1/guidance/progress/{id}` | 200 | 🔴 Critical | ⬜ |
| GD-05 | Fetch user's current progress | GET | `/api/v1/guidance/progress` | 200 | 🔴 Critical | ⬜ |

---

### 13. ⚙️ Account Settings (`test_settings.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| ST-01 | Get all user settings | GET | `/api/v1/settings/` | 200 | 🔴 Critical | ⬜ |
| ST-02 | Update basic profile settings | PATCH | `/api/v1/settings/profile` | 200 | 🟡 Important | ⬜ |
| ST-03 | Change password globally | PATCH | `/api/v1/settings/password` | 200 | 🔴 Critical | ⬜ |
| ST-04 | Update notification settings | PATCH | `/api/v1/settings/notifications`| 200 | 🟡 Important | ⬜ |
| ST-05 | Update privacy settings | PATCH | `/api/v1/settings/privacy` | 200 | 🟡 Important | ⬜ |
| ST-06 | Deactivate account (Soft Delete) | POST | `/api/v1/settings/deactivate` | 200 | 🟡 Important | ⬜ |
| ST-07 | Delete account (Hard Delete) | DELETE | `/api/v1/settings/` | 200 | 🔴 Critical | ⬜ |

---

### 14. 🤖 AI Pipeline (`test_ai_pipeline.py`)

| # | Test Scenario | Method | Endpoint | Expected Status | Priority | Status |
|---|---|---|---|---|---|---|
| AI-01 | Trigger AI pipeline analysis | POST | `/api/v1/ai/analyze` | 200 | 🔴 Critical | ⬜ |
| AI-02 | Check AI pipeline status | GET | `/api/v1/ai/analyze/status` | 200 | 🟡 Important | ⬜ |
| AI-03 | Fetch AI pipeline results | GET | `/api/v1/ai/analyze/results`| 200 | 🔴 Critical | ⬜ |

---

## 📊 Summary by Priority

| Priority | Number of Tests | Description |
|---|---|---|
| 🔴 Critical | **50** | Must pass 100%. Core business logic. |
| 🟡 Important | **47** | Crucial for smooth user experience. |
| 🟢 Nice-to-have | **4** | Admin/Maintenance utility endpoints. |
| **Total** | **101 tests** | Covers 100% of defined API endpoints. |

---

## 🗺️ Implementation Phases

### Phase 1: Foundation (Auth & Profile)
- `test_health.py`
- `test_auth.py`
- `test_users.py`
- `test_settings.py`

### Phase 2: Core Platform (Ideas & AI)
- `test_profile.py`
- `test_ideas.py`
- `test_ai_pipeline.py`
- `test_guidance.py`

### Phase 3: Collaboration & IO
- `test_groups.py`
- `test_notifications.py`
- `test_import.py`
- `test_export.py`

### Phase 4: Operations (Billing & Admin)
- `test_billing.py`
- `test_admin.py`

---
