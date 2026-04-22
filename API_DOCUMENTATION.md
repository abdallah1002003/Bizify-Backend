# 📘 Bizify API Documentation

**Base URL:** `http://localhost:8000/api/v1`  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)  
**Version:** 1.0.0

---

## 🔐 Authentication

> All protected endpoints require a Bearer token in the `Authorization` header:
> ```
> Authorization: Bearer <access_token>
> ```

---

## 1. 🔑 Authentication `/api/v1/auth`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `GET` | `/auth/google/url` | ❌ | Get Google OAuth2 redirect URL |
| `POST` | `/auth/google/callback` | ❌ | Exchange Google auth code for Bizify token |
| `POST` | `/auth/login` | ❌ | Login with email & password |
| `POST` | `/auth/logout` | ✅ | Invalidate current session token |
| `POST` | `/auth/verify-otp` | ❌ | Verify account using emailed OTP |
| `POST` | `/auth/resend-verification-otp` | ❌ | Resend account verification OTP |
| `POST` | `/auth/forgot-password` | ❌ | Send password reset code to email |
| `POST` | `/auth/reset-password` | ❌ | Reset password using OTP code |
| `GET` | `/auth/session-status` | ✅ | Get current session status & remaining time |
| `POST` | `/auth/ping` | ✅ | Keep current session alive |

### POST `/auth/login`
```json
// Request (form-data)
{
  "username": "user@example.com",
  "password": "yourpassword"
}

// Response
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### POST `/auth/verify-otp`
```json
// Request
{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

### POST `/auth/forgot-password`
```
// Query param
?email=user@example.com
```

### POST `/auth/reset-password`
```
// Query params
?email=user@example.com&otp_code=123456&new_password=NewPass123
```

### GET `/auth/session-status`
```json
// Response
{
  "is_active": true,
  "remaining_minutes": 25.5,
  "warning_threshold": 5
}
```

---

## 2. 👤 User Management `/api/v1/users`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/users/register` | ❌ | Register a new user |
| `POST` | `/users/profile` | ✅ | Update authenticated user's profile |
| `POST` | `/users/partner-profile` | ✅ | Submit partner profile with documents (multipart) |
| `PATCH` | `/users/partner-profile` | ✅ | Update partner profile info |
| `GET` | `/users/partner-profile` | ✅ | Get current user's partner profile |

### POST `/users/register`
```json
// Request
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "full_name": "John Doe"
}

// Response (201 Created)
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "USER",
  "is_active": true,
  "is_verified": false
}
```

### POST `/users/partner-profile`
```
// Request (multipart/form-data)
partner_type: "mentor" | "supplier" | "manufacturer"
user_id: "uuid-string"
files: [File1, File2, ...]   // PDF or images
company_name: "My Company"   // optional
description: "About us"      // optional
services_json: "[...]"        // optional JSON string
experience_json: "[...]"      // optional JSON string
```

---

## 3. 🗂️ User Profiling `/api/v1/profile`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `GET` | `/profile/` | ✅ | Get current user's profile |
| `POST` | `/profile/questionnaire` | ✅ | Submit onboarding questionnaire |
| `POST` | `/profile/skip` | ✅ | Skip questionnaire only |
| `POST` | `/profile/skip-guide` | ✅ | Skip beginner guide |
| `POST` | `/profile/restart` | ✅ | Reset questionnaire to start over |
| `POST` | `/profile/complete` | ✅ | Mark onboarding as completed |
| `PATCH` | `/profile/guide-status` | ✅ | Update guide status |
| `GET` | `/profile/skills` | ✅ | Get all user skills |
| `POST` | `/profile/skills` | ✅ | Add a new skill |
| `PUT` | `/profile/skills/{skill_id}` | ✅ | Update an existing skill |
| `DELETE` | `/profile/skills/{skill_id}` | ✅ | Delete a skill |

### POST `/profile/questionnaire`
```json
// Request
[
  { "question_id": "uuid", "answer": "value" },
  { "question_id": "uuid", "answer": "value" }
]
```

### POST `/profile/skills`
```json
// Request
{
  "skill_name": "Python",
  "level": "intermediate"
}
```

---

## 4. 💡 Ideas `/api/v1/ideas`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `GET` | `/ideas/` | ✅ | Get user's ideas (with filters & sorting) |
| `POST` | `/ideas/` | ✅ | Create a new business idea |
| `GET` | `/ideas/archived` | ✅ | Get archived ideas |
| `PATCH` | `/ideas/{idea_id}/archive` | ✅ | Archive a business idea |
| `PATCH` | `/ideas/{idea_id}/unarchive` | ✅ | Restore an archived idea |

### GET `/ideas/` — Query Params

| Param | Type | Description |
|-------|------|-------------|
| `min_budget` | float | Minimum budget filter |
| `max_budget` | float | Maximum budget filter |
| `skills` | string | Comma-separated (e.g. `Python,React`) |
| `feasibility` | float | Minimum feasibility score |
| `sort_by` | string | `created_at`, `budget`, `feasibility`, `ai_score` |
| `sort_order` | string | `asc` or `desc` |

### POST `/ideas/`
```json
// Request
{
  "title": "My Business Idea",
  "description": "A detailed description..."
}
```

---

## 5. 👥 Teams & Groups `/api/v1`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/groups` | ✅ | Create a new group |
| `GET` | `/groups` | ✅ | Get user's groups |
| `PATCH` | `/groups/{group_id}` | ✅ | Update a group |
| `DELETE` | `/groups/{group_id}` | ✅ | Delete a group |
| `POST` | `/groups/{group_id}/invites` | ✅ | Invite someone to a group |
| `POST` | `/groups/invites/accept` | ✅ | Accept a group invite |
| `POST` | `/groups/{group_id}/join-requests` | ✅ | Send a join request |
| `POST` | `/groups/join-requests/{request_id}/handle` | ✅ | Approve or reject join request |
| `GET` | `/groups/{group_id}/members` | ✅ | Get group members |
| `PATCH` | `/groups/members/{member_id}` | ✅ | Update member role/access |
| `DELETE` | `/groups/members/{member_id}` | ✅ | Remove a member |
| `GET` | `/groups/{group_id}/messages` | ✅ | Get group chat messages (paginated) |
| `POST` | `/groups/{group_id}/messages` | ✅ | Send a message to group chat |
| `WS` | `/groups/{group_id}/ws?token=<jwt>` | ✅ (via token) | Real-time group chat WebSocket |

### POST `/groups`
```json
// Request
{
  "name": "My Team",
  "description": "Team description"
}
```

### POST `/groups/{group_id}/invites`
```json
// Request
{
  "email": "friend@example.com",
  "role": "member",
  "idea_ids": ["uuid1", "uuid2"]
}
```

### POST `/groups/invites/accept`
```
// Query param
?token=<invite_token>
```

### POST `/groups/join-requests/{request_id}/handle`
```json
// Request
{
  "is_approved": true,
  "role": "member",
  "idea_ids": ["uuid1"]
}
```

### GET `/groups/{group_id}/messages` — Query Params

| Param | Default | Description |
|-------|---------|-------------|
| `limit` | 50 | Number of messages |
| `offset` | 0 | Skip N messages |

### WebSocket `/groups/{group_id}/ws`
```
// Connect via:
ws://localhost:8000/api/v1/groups/{group_id}/ws?token=<jwt_token>

// Send:
"Hello team!"

// Receive:
{
  "id": "uuid",
  "group_id": "uuid",
  "sender_id": "uuid",
  "sender_name": "John Doe",
  "content": "Hello team!",
  "created_at": "2024-01-01T12:00:00"
}
```

---

## 6. 🔔 Notifications `/api/v1/notifications`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `GET` | `/notifications/` | ✅ | Get paginated notifications |
| `GET` | `/notifications/stream` | ✅ | Real-time SSE notification stream |
| `GET` | `/notifications/settings` | ✅ | Get notification preferences |
| `PATCH` | `/notifications/settings` | ✅ | Update notification preferences |
| `PATCH` | `/notifications/{notification_id}/status` | ✅ | Mark as READ or DISMISSED |
| `PATCH` | `/notifications/status/bulk` | ✅ | Bulk update notification status |
| `DELETE` | `/notifications/{notification_id}` | ✅ | Delete a notification |
| `DELETE` | `/notifications/status/all` | ✅ | Delete all notifications |
| `POST` | `/notifications/bulk-delete` | ✅ | Bulk delete notifications |
| `POST` | `/notifications/test-notify` | ✅ | Send a test notification |
| `POST` | `/notifications/maintenance` | ✅ Admin only | Trigger notification cleanup |

### GET `/notifications/` — Query Params

| Param | Default | Description |
|-------|---------|-------------|
| `skip` | 0 | Offset |
| `limit` | 20 | Max 100 per page |

```json
// Response
{
  "total": 42,
  "items": [
    {
      "id": "uuid",
      "title": "New message",
      "content": "...",
      "type": "general",
      "status": "UNREAD",
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

### GET `/notifications/stream`
```
// SSE — Listen with EventSource in JS:
const es = new EventSource('/api/v1/notifications/stream', {
  headers: { Authorization: 'Bearer <token>' }
});
es.onmessage = (e) => console.log(JSON.parse(e.data));
```

### PATCH `/notifications/{notification_id}/status`
```json
// Request
{
  "status": "READ"   // or "DISMISSED"
}
```

### PATCH `/notifications/status/bulk`
```json
// Request
{
  "notification_ids": ["uuid1", "uuid2"],
  "status": "READ"
}
```

---

## 7. ⚙️ User Settings `/api/v1/settings`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `GET` | `/settings/` | ✅ | Get all settings (profile, notifications, privacy) |
| `PATCH` | `/settings/profile` | ✅ | Update profile information |
| `PATCH` | `/settings/password` | ✅ | Change password + global logout |
| `PATCH` | `/settings/notifications` | ✅ | Update notification settings |
| `PATCH` | `/settings/privacy` | ✅ | Update privacy settings |
| `POST` | `/settings/deactivate` | ✅ | Soft-delete account |
| `DELETE` | `/settings/` | ✅ | Permanently delete account |

### GET `/settings/` Response
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "last_password_change": "2024-01-01T12:00:00",
  "notifications": { ... },
  "privacy": { ... }
}
```

### PATCH `/settings/password`
```json
// Request
{
  "current_password": "OldPass123",
  "new_password": "NewPass456"
}
```

---

## 8. 📚 Business Guidance `/api/v1/guidance`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `GET` | `/guidance/stages` | ❌ | Get all guidance stages (ordered by sequence) |
| `GET` | `/guidance/stages/{stage_id}/concepts` | ❌ | Get all concepts for a stage |
| `GET` | `/guidance/concepts/{concept_id}` | ❌ | Get details of a specific concept |
| `POST` | `/guidance/progress/{concept_id}` | ✅ | Mark concept as viewed / update progress |
| `GET` | `/guidance/progress` | ✅ | Get last user progress point |

---

## 9. 💳 Billing `/api/v1/billing`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `GET` | `/billing/plans` | ❌ | Get all active subscription plans |
| `GET` | `/billing/subscription` | ✅ | Get user's active subscription |
| `DELETE` | `/billing/subscription` | ✅ | Cancel active subscription |
| `POST` | `/billing/paypal/subscribe` | ✅ | Create PayPal order for a plan |
| `POST` | `/billing/paypal/capture` | ✅ | Capture PayPal order after user approval |
| `POST` | `/billing/paypal/webhook` | ❌ | PayPal webhook callback (internal) |
| `POST` | `/billing/paymob/subscribe` | ✅ | Initiate Paymob card payment (Visa/Mastercard) |
| `POST` | `/billing/paymob/webhook` | ❌ | Paymob webhook callback (internal) |

### POST `/billing/paypal/subscribe`
```json
// Request
{
  "plan_id": "uuid"
}

// Response
{
  "order_id": "PAYPAL-ORDER-ID",
  "approval_url": "https://www.paypal.com/checkoutnow?token=..."
}
```

### POST `/billing/paypal/capture`
```json
// Request
{
  "order_id": "PAYPAL-ORDER-ID",
  "plan_id": "uuid"
}
```

### POST `/billing/paymob/subscribe`
```json
// Request
{
  "plan_id": "uuid",
  "first_name": "John",       // optional
  "last_name": "Doe",         // optional
  "email": "john@example.com", // optional
  "phone_number": "+201012345678" // optional
}

// Response
{
  "iframe_url": "https://accept.paymob.com/api/acceptance/iframes/..."
}
// → Render this URL inside an <iframe> for the user to enter card details
```

---

## 10. 📤 Export `/api/v1/export`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/export/` | ✅ | Start a new data export job |
| `GET` | `/export/{job_id}` | ✅ | Get export job status |
| `POST` | `/export/{job_id}/cancel` | ✅ | Cancel an export job |
| `GET` | `/export/{job_id}/download` | ✅ | Download completed export file |

### POST `/export/`
```json
// Request
{
  "scope": "ideas",     // or "profile", "all"
  "format": "pdf"       // or "json", "word"
}

// Response
{
  "id": "job-uuid",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00"
}
```

---

## 11. 📥 Import `/api/v1/import`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/import/upload` | ✅ | Upload & process a document |
| `DELETE` | `/import/{document_id}` | ✅ | Delete a document |
| `GET` | `/import/{document_id}/export-ai` | ✅ | Get extracted text for AI workflows |

### POST `/import/upload`
```
// Request (multipart/form-data)
file: <File>

// Response
{
  "message": "Document uploaded and processed successfully!",
  "document_id": "uuid",
  "filename": "document.pdf"
}
```

---

## 12. 🛡️ Admin `/api/v1/admin`

> ⚠️ All admin endpoints require **ADMIN role**.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/users` | Get all users (paginated) |
| `GET` | `/admin/users/search?email=...` | Search user by email |
| `DELETE` | `/admin/users?email=...` | Delete user by email |
| `PATCH` | `/admin/users/{user_id}/promote` | Promote user to a new role |
| `PATCH` | `/admin/users/{user_id}/suspend` | Suspend a user |
| `GET` | `/admin/requests` | List partner requests (filterable by status) |
| `PATCH` | `/admin/approve/{profile_id}` | Approve a partner request |
| `PATCH` | `/admin/reject/{profile_id}` | Reject a partner request |
| `GET` | `/admin/security-logs` | View all security logs |
| `GET` | `/admin/stats` | Get dashboard statistics |

### GET `/admin/requests` — Query Params
```
?status=pending   // or: approved, rejected
```

### PATCH `/admin/users/{user_id}/promote`
```
?new_role=admin   // or: user, partner
```

### GET `/admin/stats` Response
```json
{
  "total_users": 150,
  "active_subscriptions": 42,
  "pending_partner_requests": 5,
  ...
}
```

---

## 🌐 Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Simple connectivity test |
| `GET` | `/health` | Service health status |

---

## 📌 Quick Reference

| Category | Base Path |
|----------|-----------|
| Authentication | `/api/v1/auth` |
| Users | `/api/v1/users` |
| Profile & Onboarding | `/api/v1/profile` |
| Ideas | `/api/v1/ideas` |
| Teams / Groups | `/api/v1/groups` |
| Notifications | `/api/v1/notifications` |
| Settings | `/api/v1/settings` |
| Business Guidance | `/api/v1/guidance` |
| Billing (PayPal + Paymob) | `/api/v1/billing` |
| Export | `/api/v1/export` |
| Import | `/api/v1/import` |
| Admin | `/api/v1/admin` |

---

## 🧪 Import in Postman
