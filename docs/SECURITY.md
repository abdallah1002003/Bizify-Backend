# Bizify — Security & Access Control

Bizify implements a robust security model to protect user data, ensure proper authorization across different roles, and mitigate common web vulnerabilities.

## 1. Authentication Mechanisms

| Feature | Implementation Detail |
|---|---|
| **JWT Auth** | Uses `python-jose` with the HS256 algorithm to generate and validate stateless Bearer tokens. |
| **Password Hashing** | Uses `passlib` with `bcrypt` (pinned to `<4.0.0` for compatibility). Raw passwords are never stored. |
| **Token Revocation** | When a user logs out, their JWT string is saved to the `token_blacklist` table, invalidating it immediately. |

## 2. Session Management & Expiry

| Mechanism | Description |
|---|---|
| **Inactivity Timeout** | Sessions expire if `last_activity` exceeds `SESSION_TIMEOUT_MINUTES`. Calling `/auth/ping` refreshes this timestamp. |
| **Global Revocation** | `last_password_change` and `revoked_at` timestamps on the `User` model invalidate all older JWTs globally, forcing a re-login across all devices. |

## 3. Account Protection

| Protection | Description |
|---|---|
| **Brute Force Protection** | 5 failed password attempts trigger a 15-minute temporary lock (`locked_until` field on `User`). |
| **OTP Verification** | Account verification and password resets require 6-digit OTPs. OTPs have a 10-minute expiration window and a 60-second cooldown to prevent spam. |
| **Account Suspension** | Admins can suspend users, setting `is_active=False` and recording the time in `revoked_at`. |

## 4. Authorization & Access Control

| Scope | Rules |
|---|---|
| **Role-Based Access Control (RBAC)** | `RoleChecker([UserRole.ADMIN])` dependency protects admin routes. Unauthorized attempts are automatically logged to the `security_logs` table. |
| **Group / Team Access** | Access to group chat or group settings requires either (1) owning the parent business, (2) being an active member of the group, or (3) holding a specific group role (`OWNER`, `EDITOR`, `VIEWER`). |
| **IDOR Protection** | Resources like documents, notifications, export jobs, custom skills, and ideas are strictly scoped to `current_user.id` in repository queries. Users cannot access resources belonging to other users simply by guessing UUIDs. |

## 5. Rate Limiting

> ⚠️ **Not currently implemented.** No rate limiting middleware (e.g., `slowapi`) is applied to any endpoint in the current version (`0.1.0`).

The application mitigates abuse through application-level controls instead:

| Control | Scope | Limit |
|---|---|---|
| Login brute-force lockout | `POST /auth/login` | 5 failed attempts → 15-min lock |
| OTP resend cooldown | `/auth/resend-verification-otp`, `/auth/forgot-password` | 60-second cooldown |

**Planned (Future Release):** Global API rate limiting using `slowapi` (a FastAPI wrapper around `limits`). Recommended limits for production:
- Public endpoints (login, register): **10 req/min per IP**
- Protected endpoints: **60 req/min per user**
- Export/AI pipeline: **5 req/min per user**

## 6. Audit Logging

Security-sensitive events are recorded for accountability:

- **Security Logs:** Failed logins, unauthorized admin access attempts, locked accounts.
- **Audit Logs:** Successful logins, password changes, token revocations.
- **Admin Logs:** Promotions, user suspensions, partner approvals/rejections.
