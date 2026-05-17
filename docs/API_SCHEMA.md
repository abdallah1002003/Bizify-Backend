# Bizify API Documentation

**Base URL:** `https://bizify-backend.onrender.com`
**Swagger UI:** `https://bizify-backend.onrender.com/docs`

---

## Authentication

**All endpoints require** `Authorization: Bearer <token>` **in the header** (except login, register, health).

### How to get a token

1. **Register:**
   ```
   POST /api/v1/users/register
   {"email": "...", "password": "...", "confirm_password": "...", "full_name": "..."}
   ```
   Returns: `{"detail": "SMTP blocked. Verification code: 123456"}`

2. **Verify OTP:**
   ```
   POST /api/v1/auth/verify-otp
   {"email": "...", "otp_code": "123456"}
   ```
   Returns: `{"message": "Account verified successfully"}`

3. **Login:**
   ```
   POST /api/v1/auth/login
   Body: username=email&password=...
   Content-Type: application/x-www-form-urlencoded
   ```
   Returns: `{"access_token": "eyJ...", "token_type": "bearer"}`

4. **Use token:** Add header `Authorization: Bearer eyJ...` to every request.

---

## Endpoints

### Health
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | - | Server health check |

### Auth (`/api/v1/auth`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| GET | `/google/url` | - | `{"url": "..."}` | - |
| POST | `/google/callback` | `{"code": "..."}` | Token | - |
| POST | `/login` | `username=email&password=...` (form) | Token | - |
| POST | `/logout` | - | `{"message": "..."}` | ✅ |
| POST | `/verify-otp` | `{"email": "...", "otp_code": "..."}` | `{"message": "..."}` | - |
| POST | `/resend-verification-otp` | `{"email": "..."}` | `{"message": "..."}` | - |
| POST | `/forgot-password` | `?email=...` | `{"message": "..."}` | - |
| POST | `/verify-reset-code` | `?email=...&otp_code=...` | `{"message": "..."}` | - |
| POST | `/reset-password` | `?email=...&otp_code=...&new_password=...` | `{"message": "..."}` | - |
| GET | `/session-status` | - | session info | ✅ |
| POST | `/ping` | - | `{"message": "..."}` | ✅ |

### Users (`/api/v1/users`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| POST | `/register` | `EntrepreneurRegistration` | UserRead (201) | - |
| POST | `/register-partner` | Multipart form (files + fields) | UserRead (201) | - |
| POST | `/profile` | `UserProfileUpdate` | UserProfileRead | ✅ |
| GET | `/partner-profile` | - | PartnerProfileRead | ✅ |
| POST | `/partner-profile` | Multipart form | PartnerProfileRead (201) | ✅ |
| PATCH | `/partner-profile` | `PartnerProfileUpdate` | PartnerProfileRead | ✅ |

### AI Pipeline (`/api/v1/ai`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| POST | `/general-chat` | `{"message": "...", "history": [...]}` | `{"response": "...", "history": [...]}` | ✅ |
| POST | `/general-chat/stream` | `{"message": "...", "history": [...]}` | SSE stream | ✅ |
| POST | `/run` | `{}` | JSON | ✅ |
| GET | `/profile` | - | JSON | ✅ |
| GET | `/problems` | - | JSON | ✅ |
| GET | `/customers` | - | JSON | ✅ |
| GET | `/competition` | - | JSON | ✅ |
| GET | `/market-potential` | - | JSON | ✅ |
| GET | `/idea-strategy` | - | JSON | ✅ |
| GET | `/business-model` | - | JSON | ✅ |
| GET | `/functions-list` | - | JSON | ✅ |
| GET | `/mvp-planning` | - | JSON | ✅ |
| GET | `/unit-economics` | - | JSON | ✅ |
| GET | `/go-to-market` | - | JSON | ✅ |
| GET | `/idea` | - | JSON | ✅ |

### Marketplace (`/api/v1/marketplace`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| GET | `/partners` | `?type=MENTOR&q=search&skip=0&limit=50` | `[MarketplacePartnerPublic]` | ✅ |
| GET | `/partners/{id}` | - | MarketplacePartnerPublic | ✅ |
| POST | `/partners/{id}/requests` | `{"business_id": "..."}` | MarketplacePartnerRequestRead (201) | ✅ |
| GET | `/requests` | `?skip=0&limit=100` | `[MarketplacePartnerRequestRead]` | ✅ |

### Profile (`/api/v1/profile`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| GET | `/` | - | UserProfileRead | ✅ |
| POST | `/questionnaire` | `[QuestionnaireAnswer]` | QuestionnaireResponse | ✅ |
| GET | `/questionnaire` | - | JSON | ✅ |
| POST | `/skip` | - | `{"message": "..."}` | ✅ |
| POST | `/restart` | - | `{"message": "..."}` | ✅ |
| POST | `/complete` | - | `{"message": "..."}` | ✅ |
| GET | `/skill-categories` | - | `[string]` | ✅ |
| GET | `/skills` | - | `[dict]` | ✅ |
| GET | `/skills/search` | `?q=...` | `[string]` | ✅ |
| POST | `/skills` | `{...}` | `{...}` (201) | ✅ |
| DELETE | `/skills/{id}` | - | 204 | ✅ |
| GET | `/skills/json` | - | JSON | ✅ |
| POST | `/skills/json` | `{...}` | JSON | ✅ |

### Ideas (`/api/v1/ideas`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| GET | `/` | `?min_budget=&max_budget=&skills=&feasibility=&sort_by=&sort_order=` | `[IdeaRead]` | ✅ |
| POST | `/` | `IdeaCreate` | IdeaRead (201) | ✅ |
| GET | `/archived` | - | `[IdeaRead]` | ✅ |
| PATCH | `/{id}/archive` | - | IdeaRead | ✅ |
| PATCH | `/{id}/unarchive` | - | IdeaRead | ✅ |

### Groups (`/api/v1/groups`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| POST | `/groups` | `GroupCreate` | GroupResponse (201) | ✅ |
| GET | `/groups` | - | `[GroupResponse]` | ✅ |
| PATCH | `/groups/{id}` | `GroupUpdate` | GroupResponse | ✅ |
| DELETE | `/groups/{id}` | - | `{"message": "..."}` | ✅ |
| POST | `/groups/{id}/invites` | `{"email": "...", "role": "..."}` | `{...}` | ✅ |
| POST | `/groups/invites/accept` | `?token=...` | `{...}` | ✅ |
| POST | `/groups/{id}/join-requests` | - | `{...}` | ✅ |
| POST | `/groups/join-requests/{id}/handle` | `{"is_approved": true}` | `{...}` | ✅ |
| GET | `/groups/{id}/members` | - | `[GroupMemberResponse]` | ✅ |
| PATCH | `/groups/members/{id}` | `GroupMemberUpdate` | GroupMemberResponse | ✅ |
| DELETE | `/groups/members/{id}` | - | `{"message": "..."}` | ✅ |
| GET | `/groups/{id}/messages` | `?limit=50&offset=0` | `[GroupMessageResponse]` | ✅ |
| POST | `/groups/{id}/messages` | `{"content": "..."}` | GroupMessageResponse (201) | ✅ |
| WS | `/groups/{id}/ws` | `?token=...` | WebSocket | token |

### Notifications (`/api/v1/notifications`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| GET | `/` | `?skip=0&limit=20` | `NotificationList` | ✅ |
| GET | `/stream` | - | SSE stream | ✅ |
| PATCH | `/{id}/status` | `{"status": "..."}` | NotificationRead | ✅ |
| PATCH | `/status/bulk` | `{"notification_ids": [...], "status": "..."}` | `{"message": "..."}` | ✅ |
| GET | `/settings` | - | NotificationSettingRead | ✅ |
| PATCH | `/settings` | `NotificationSettingUpdate` | NotificationSettingRead | ✅ |
| DELETE | `/{id}` | - | 204 | ✅ |
| POST | `/bulk-delete` | `{"notification_ids": [...]}` | `{"message": "..."}` | ✅ |
| DELETE | `/status/all` | - | `{"message": "..."}` | ✅ |

### Settings (`/api/v1/settings`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| GET | `/` | - | SettingsResponse | ✅ |
| PATCH | `/profile` | `ProfileUpdate` | UserProfileRead | ✅ |
| PATCH | `/password` | `{"current_password": "...", "new_password": "...", "confirm_password": "..."}` | `{"message": "..."}` | ✅ |
| PATCH | `/notifications` | `NotificationUpdate` | NotificationUpdate | ✅ |
| PATCH | `/privacy` | `PrivacyUpdate` | PrivacyUpdate | ✅ |
| POST | `/deactivate` | - | `{"message": "..."}` | ✅ |
| DELETE | `/` | - | `{"message": "..."}` | ✅ |

### Billing (`/api/v1/billing`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| GET | `/plans` | - | `[PlanRead]` | - |
| POST | `/paypal/subscribe` | `{"plan_id": "..."}` | OrderResponse | ✅ |
| POST | `/paypal/capture` | `{"order_id": "...", "plan_id": "..."}` | CaptureResponse | ✅ |
| GET | `/subscription` | - | SubscriptionRead | ✅ |
| DELETE | `/subscription` | - | `{"message": "..."}` | ✅ |
| POST | `/paypal/webhook` | PayPal headers + body | `{"message": "..."}` | - |
| POST | `/paymob/subscribe` | `PaymobCheckoutRequest` | PaymobCheckoutResponse | ✅ |
| POST | `/paymob/webhook` | JSON body | `{"message": "..."}` | - |

### Payment Methods (`/api/v1/payment-methods`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| GET | `/` | - | `[PaymentMethodRead]` | ✅ |
| POST | `/` | `PaymentMethodCreate` | PaymentMethodRead (201) | ✅ |
| PUT | `/{id}/default` | - | PaymentMethodRead | ✅ |
| DELETE | `/{id}` | - | 204 | ✅ |

### Export (`/api/v1/export`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| POST | `/` | `{"scope": [...], "format": "pdf"}` | ExportJobResponse | ✅ |
| GET | `/{id}` | - | ExportJobResponse | ✅ |
| GET | `/{id}/download` | - | File download | ✅ |
| POST | `/{id}/cancel` | - | `{"message": "..."}` | ✅ |

### Import (`/api/v1/import`)
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| POST | `/upload` | Multipart: `file` | `{...}` | ✅ |
| DELETE | `/{id}` | - | `{"message": "..."}` | ✅ |
| GET | `/{id}/export-ai` | - | `{...}` | ✅ |

### Admin (`/api/v1/admin`) — Admin role only
| Method | Path | Request | Response | Auth |
|--------|------|---------|----------|------|
| GET | `/requests` | `?status=PENDING` | `[PartnerProfileRead]` | Admin |
| GET | `/users/search` | `?email=...` | UserRead | Admin |
| DELETE | `/users` | `?email=...` | 204 | Admin |
| GET | `/users` | `?skip=0&limit=100` | `[UserRead]` | Admin |
| GET | `/stats` | - | `{...}` | Admin |
| PATCH | `/approve/{id}` | - | PartnerProfileRead | Admin |
| PATCH | `/reject/{id}` | - | PartnerProfileRead | Admin |
| PATCH | `/users/{id}/promote` | `?new_role=...` | UserRead | Admin |
| PATCH | `/users/{id}/suspend` | - | UserRead | Admin |
| GET | `/security-logs` | - | `[SecurityLogRead]` | Admin |

---

## Schema Reference

### User Schemas

**`EntrepreneurRegistration`** / **`UserCreate`**
```json
{
  "email": "user@example.com",
  "password": "string (min 8 chars)",
  "confirm_password": "string",
  "full_name": "string (optional)",
  "role": "ENTREPRENEUR | MENTOR | SUPPLIER | MANUFACTURER | ADMIN"
}
```

**`UserRead`**
```json
{
  "id": "uuid",
  "email": "email",
  "full_name": "string (optional)",
  "role": "ENTREPRENEUR",
  "is_active": true,
  "is_verified": false,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**`Token`**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

### AI Pipeline Schemas

**`GeneralChatRequest`**
```json
{
  "message": "hello",
  "history": []
}
```

**`GeneralChatResponse`**
```json
{
  "response": "Hello! I'm bizifyAI...",
  "history": [
    {"role": "user", "content": "hello"},
    {"role": "assistant", "content": "Hello! I'm bizifyAI..."}
  ]
}
```

### Marketplace Schemas

**`MarketplacePartnerPublic`**
```json
{
  "id": "uuid",
  "partner_type": "MENTOR | SUPPLIER | MANUFACTURER",
  "company_name": "string",
  "description": "string",
  "services_json": {"services": ["..."]},
  "experience_json": {"years": 10, "industries": ["..."]},
  "display_name": "string"
}
```

### Profile Schemas

**`QuestionnaireAnswer`**
```json
{
  "field": "experience_level",
  "question": "How many years of experience do you have?",
  "multi": false,
  "choices": ["0-2", "3-5", "5-10", "10+"],
  "label": "Intermediate (3-5 years)
"
}
```

**`QuestionnaireResponse`**
```json
{
  "user_profile": {
    "curiosity_domain": "...",
    "experience_level": "...",
    "business_interests": ["..."],
    "target_region": "...",
    "founder_setup": "...",
    "risk_tolerance": "..."
  },
  "career_profile": {
    "free_day_preferences": ["..."],
    "preferred_work_types": ["..."],
    "problem_solving_styles": ["..."],
    "preferred_work_environments": ["..."],
    "desired_impact": ["..."]
  }
}
```

### Group Schemas

**`GroupCreate`**
```json
{
  "name": "My Team (min 3 chars)",
  "description": "optional",
  "default_role": "VIEWER | EDITOR | ADMIN",
  "is_chat_enabled": true
}
```

**`GroupResponse`**
```json
{
  "id": "uuid",
  "name": "My Team",
  "description": null,
  "default_role": "VIEWER",
  "is_chat_enabled": true,
  "business_id": "uuid",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**`GroupMemberResponse`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "group_id": "uuid",
  "email": "user@example.com",
  "role": "VIEWER",
  "status": "ACTIVE | PENDING | INACTIVE",
  "accessible_ideas": [{"id": "uuid", "title": "..."}],
  "joined_at": "datetime"
}
```

**`GroupInviteCreate`**
```json
{
  "email": "user@example.com",
  "role": "VIEWER (optional)",
  "idea_ids": ["uuid", "uuid"] (optional)
}
```

### Idea Schemas

**`IdeaCreate`**
```json
{
  "title": "My Idea",
  "description": "optional",
  "status": "DRAFT | ACTIVE | COMPLETED | ARCHIVED",
  "budget": 50000.0,
  "skills": ["Python", "Marketing"],
  "feasibility": 7.5
}
```

**`IdeaRead`**
```json
{
  "id": "uuid",
  "title": "My Idea",
  "description": null,
  "status": "DRAFT",
  "is_archived": false,
  "budget": null,
  "skills": null,
  "feasibility": null,
  "owner_id": "uuid",
  "business_id": null,
  "archived_at": null,
  "created_at": "datetime",
  "updated_at": "datetime",
  "converted_at": null
}
```

### Billing Schemas

**`PlanRead`**
```json
{
  "id": "uuid",
  "name": "Pro Plan",
  "price": 29.99,
  "features_json": {},
  "is_active": true
}
```

**`SubscriptionRead`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "plan_id": "uuid",
  "status": "ACTIVE | CANCELLED | EXPIRED",
  "start_date": "datetime",
  "end_date": null,
  "paypal_subscription_id": null,
  "plan": null
}
```

### Notification Schemas

**`NotificationRead`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "New Message",
  "content": "You have a new message...",
  "type": "info | warning | error | success",
  "status": "UNREAD | READ | ARCHIVED",
  "delivery_status": "SENT | DELIVERED | FAILED",
  "expires_at": null,
  "created_at": "datetime"
}
```

### Settings Schemas

**`PasswordChange`**
```json
{
  "current_password": "oldpass123",
  "new_password": "newpass123 (min 8 chars)",
  "confirm_password": "newpass123"
}
```

**`ProfileUpdate`**
```json
{
  "full_name": "New Name",
  "bio": "About me...",
  "interests": ["coding", "design"]
}
```

### Export Schemas

**`ExportRequest`**
```json
{
  "scope": ["profile", "skills", "ideas"],
  "format": "pdf"
}
```

### Partner/Admin Schemas

**`PartnerProfileRead`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "partner_type": "MENTOR | SUPPLIER | MANUFACTURER",
  "company_name": "string",
  "description": "string",
  "services_json": {},
  "experience_json": {},
  "approval_status": "PENDING | APPROVED | REJECTED",
  "approved_by": null,
  "documents_json": null,
  "approved_at": null,
  "created_at": "datetime"
}
```

### Payment Method Schemas

**`PaymentMethodCreate`**
```json
{
  "user_id": "uuid",
  "provider": "visa | mastercard | paypal",
  "token_ref": "token_from_provider",
  "last4": "4242",
  "is_default": false
}
```

---

## Roles

| Role | Description |
|------|-------------|
| `ENTREPRENEUR` | Default user role |
| `MENTOR` | Mentor partner |
| `SUPPLIER` | Supplier partner |
| `MANUFACTURER` | Manufacturer partner |
| `ADMIN` | Admin (full access) |

## Partner Types
| Type | Description |
|------|-------------|
| `MENTOR` | Business mentor/advisor |
| `SUPPLIER` | Service/product supplier |
| `MANUFACTURER` | Manufacturing partner |

## Common Enums

- **GuideStatus:** `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`
- **ApprovalStatus:** `PENDING`, `APPROVED`, `REJECTED`
- **RequestStatus:** `PENDING`, `APPROVED`, `REJECTED`
- **GroupRole:** `VIEWER`, `EDITOR`, `OWNER`
- **GroupMemberStatus:** `ACTIVE`, `PENDING`, `INACTIVE`
- **GroupInviteStatus:** `PENDING`, `ACCEPTED`, `REJECTED`, `EXPIRED`
- **GroupJoinRequestStatus:** `PENDING`, `APPROVED`, `REJECTED`
- **IdeaStatus:** `DRAFT`, `ACTIVE`, `COMPLETED`, `ARCHIVED`
- **SubscriptionStatus:** `ACTIVE`, `CANCELLED`, `EXPIRED`
- **NotificationStatus:** `UNREAD`, `READ`, `ARCHIVED`
- **DeliveryStatus:** `SENT`, `DELIVERED`, `FAILED`
- **ProfileVisibility:** `PUBLIC`, `PRIVATE`, `TEAM_ONLY`
- **BusinessStage:** `EARLY`, `GROWTH`, `MATURE`
- **ExportStatus:** `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`
