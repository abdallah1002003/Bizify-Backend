# API Routes Quick Reference

## Route Prefixes and Endpoints

```
/auth
  ├── POST /login

/users
  ├── GET /
  ├── POST /
  ├── GET /me
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/user_profiles (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/admin_action_logs (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/partner_profiles (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/partner_requests (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/ideas
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/idea_versions (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/idea_metrics (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/experiments (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/businesses
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/business_collaborators (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/business_invites (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/business_invite_ideas (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/idea_access (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/business_roadmaps (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/roadmap_stages (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/agents (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/agent_runs (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/validation_logs (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/embeddings (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/chat_sessions (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/chat_messages (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/plans (Auth Required)
  ├── GET /
  ├── POST / (Admin Only)
  ├── GET /{id}
  ├── PUT /{id} (Admin Only)
  └── DELETE /{id} (Admin Only)

/subscriptions (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/payment_methods (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/payments (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/usages (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/files (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/notifications (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/share_links (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/idea_comparisons (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/comparison_items (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}

/comparison_metrics (Auth Required)
  ├── GET /
  ├── POST /
  ├── GET /{id}
  ├── PUT /{id}
  └── DELETE /{id}
```

## Quick Stats

| Metric | Count |
|--------|-------|
| Total Routes | 1 |
| Total Endpoints | 36 |
| Total Operations (CRUD) | 180 |
| Auth Required Endpoints | 28 |
| Public Endpoints | 8 |
| Admin-Only Operations | 3 |

### Breakdown by Module
- **Auth**: 1 endpoint
- **Users**: 3 endpoints
- **Profiles**: 2 endpoints (User, Partner)
- **Admin**: 1 endpoint
- **Ideation**: 8 endpoints
- **Business**: 6 endpoints
- **AI**: 4 endpoints
- **Chat**: 2 endpoints
- **Billing**: 5 endpoints
- **Core**: 3 endpoints
- **Partners**: 2 endpoints

## Authentication Methods

### Login (Public)
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

### Protected Endpoints
```bash
Authorization: Bearer {access_token}
```

## Common Query Parameters

### List Endpoints
- `skip` (int, default=0): Pagination offset
- `limit` (int, default=100): Max results

## Access Control Patterns

### Public Routes (No Auth)
- `/auth/login`
- `/users` (POST only - registration)

### User-Scoped Routes (Auth Required)
Returns/modifies only current user's data
- Billing routes
- Chat routes
- File, Notification, Share Link routes

### Ownership-Protected Routes
Requires user to own the resource
- Ideas (owner_id)
- Businesses (owner_id)
- Chat Sessions (user_id)

### Admin-Only Routes
Requires ADMIN role
- Plans: POST, PUT, DELETE

## CRUD Operations Summary

### Standard CRUD
```
GET  /resource/          → List all
POST /resource/          → Create
GET  /resource/{id}      → Read one
PUT  /resource/{id}      → Update
DELETE /resource/{id}    → Delete
```

### Special Endpoints
- `GET /users/me` → Get current user
- `GET /auth/login` → Login (POST only)

## HTTP Status Codes Reference

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST |
| 204 | No Content | Delete success (no body) |
| 400 | Bad Request | Invalid input |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal error |

## Response Format Templates

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Single Resource
```json
{
  "id": "uuid",
  "field1": "value1",
  "created_at": "2026-02-21T00:00:00Z",
  "updated_at": "2026-02-21T00:00:00Z"
}
```

### List Response
```json
{
  "items": [
    { "id": "uuid1", ... },
    { "id": "uuid2", ... }
  ],
  "total": 100,
  "skip": 0,
  "limit": 10
}
```

## Modules by Feature

### User Management
- `/users` - User CRUD
- `/user_profiles` - User profile data
- `/admin_action_logs` - Admin actions

### Ideas & Ideation
- `/ideas` - Main idea entity
- `/idea_versions` - Idea version history
- `/idea_metrics` - Idea metrics
- `/idea_access` - Access control
- `/idea_comparisons` - Compare ideas
- `/comparison_items` - Comparison details
- `/comparison_metrics` - Comparison metrics
- `/experiments` - Experiments on ideas

### Business Management
- `/businesses` - Company/business entity
- `/business_collaborators` - Team members
- `/business_invites` - Invite others
- `/business_invite_ideas` - Ideas to business
- `/business_roadmaps` - Business roadmap
- `/roadmap_stages` - Roadmap phases

### AI & Automation
- `/agents` - AI agent templates
- `/agent_runs` - Agent executions
- `/validation_logs` - AI validation/critique
- `/embeddings` - Vector embeddings

### Communication
- `/chat_sessions` - Chat conversation threads
- `/chat_messages` - Individual messages

### Billing & Payments
- `/plans` - Subscription plans
- `/subscriptions` - User subscriptions
- `/payment_methods` - Stored payment methods
- `/payments` - Payment transactions
- `/usages` - Usage tracking

### Core Features
- `/files` - File storage
- `/notifications` - User notifications
- `/share_links` - Public sharing links

### Partnerships
- `/partner_profiles` - Partner accounts
- `/partner_requests` - Partnership requests

## File Organization

```
app/api/routes/
├── auth.py                          → /auth
├── users/
│   ├── user.py                      → /users
│   ├── user_profile.py              → /user_profiles
│   └── admin_action_log.py          → /admin_action_logs
├── ideation/
│   ├── idea.py                      → /ideas
│   ├── idea_version.py              → /idea_versions
│   ├── idea_metric.py               → /idea_metrics
│   ├── idea_access.py               → /idea_access
│   ├── idea_comparison.py           → /idea_comparisons
│   ├── comparison_item.py           → /comparison_items
│   ├── comparison_metric.py         → /comparison_metrics
│   └── experiment.py                → /experiments
├── business/
│   ├── business.py                  → /businesses
│   ├── business_collaborator.py     → /business_collaborators
│   ├── business_invite.py           → /business_invites
│   ├── business_invite_idea.py      → /business_invite_ideas
│   ├── business_roadmap.py          → /business_roadmaps
│   └── roadmap_stage.py             → /roadmap_stages
├── ai/
│   ├── agent.py                     → /agents
│   ├── agent_run.py                 → /agent_runs
│   ├── validation_log.py            → /validation_logs
│   └── embedding.py                 → /embeddings
├── chat/
│   ├── chat_session.py              → /chat_sessions
│   └── chat_message.py              → /chat_messages
├── billing/
│   ├── plan.py                      → /plans
│   ├── subscription.py              → /subscriptions
│   ├── payment_method.py            → /payment_methods
│   ├── payment.py                   → /payments
│   └── usage.py                     → /usages
├── core/
│   ├── file.py                      → /files
│   ├── notification.py              → /notifications
│   └── share_link.py                → /share_links
├── partners/
│   ├── partner_profile.py           → /partner_profiles
│   └── partner_request.py           → /partner_requests
└── api.py                           → Router configuration
```

## Testing Routes

### Login and Get Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password"
```

### Use Token on Protected Route
```bash
curl -X GET http://localhost:8000/api/v1/ideas \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

**Generated:** February 21, 2026  
**Total Routes Documented:** 36  
**Total CRUD Operations:** 180
