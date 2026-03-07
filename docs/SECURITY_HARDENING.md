# Security Hardening Guide

This document details security implementation and recommendations for the Bizify application.

## 🔒 Current Security Features

### Secret Key Management
- **Default**: `"change-me-in-env"` (placeholder)
- **Validation**: Non-test environments require 32+ character keys
- **Status**: ✅ Enforced via Pydantic validator in settings.py (lines 95-115)
- **Production Requirement**: Must be generated and unique per deployment

```python
# ✅ GOOD - In production .env:
SECRET_KEY=your-generated-256-bit-random-key-with-32plus-chars

# ❌ BAD - Using default:
SECRET_KEY=change-me-in-env  # Will raise ValueError on app startup
```

### JWT Token Cryptography
- **Algorithms**: RS256 (asymmetric, production) or HS256 (symmetric, fallback)
- **RS256 Priority**: When JWT_PRIVATE_KEY is configured, RS256 is used automatically
- **Key Generation**: `python scripts/generate_rsa_keys.py`
- **Status**: ✅ Implemented with automatic algo selection (jwt_algorithm property)

```python
# Production setup (config/settings.py):
JWT_ALGORITHM: str = "RS256"  # When RSA keys are configured
JWT_PRIVATE_KEY: str = ""     # PEM format
JWT_PUBLIC_KEY: str = ""      # PEM format
```

### Admin Bootstrap Endpoint (`POST /api/v1/auth/bootstrap-admin`)

**Purpose**: Create initial admin account during deployment (one-time only)

#### Configuration
```env
# .env file:
ALLOW_ADMIN_BOOTSTRAP=false          # Default: disabled
ADMIN_BOOTSTRAP_TOKEN=""             # Must be set to enable bootstrap
APP_ENV=production                   # Environment
```

#### Security Checks (app/api/routes/auth.py, lines 100-155)
1. **Bootstrap Disabled by Default**: `if not settings.ALLOW_ADMIN_BOOTSTRAP` → HTTP 403
2. **Token Validation**:
   - Checks if ADMIN_BOOTSTRAP_TOKEN is configured
   - Validates exact token match from X-Bootstrap-Token header
   - Fails with HTTP 403 if invalid
3. **Idempotency Check**: Rejects bootstrap if admin already exists (HTTP 409)
4. **Email Uniqueness**: Rejects if email already registered (HTTP 409)
5. **Rate Limiting**: 3 attempts per minute via Redis middleware (app/middleware/rate_limiter_redis.py)

#### Safe Procedure
```bash
# 1. Generate bootstrap token (e.g., 32+ random chars)
$ openssl rand -hex 32

# 2. Set in .env (before deployment)
ALLOW_ADMIN_BOOTSTRAP=true
ADMIN_BOOTSTRAP_TOKEN=<generated-token>
APP_ENV=staging  # Or temporary production

# 3. Call bootstrap endpoint ONCE
curl -X POST "http://api.example.com/api/v1/auth/bootstrap-admin" \
  -H "Content-Type: application/json" \
  -H "X-Bootstrap-Token: <token>" \
  -d '{
    "name": "Admin User",
    "email": "admin@example.com",
    "password": "strong-password-min-8-chars"
  }'

# 4. Verify success (returns access_token, refresh_token)

# 5. IMMEDIATELY disable bootstrap in .env
ALLOW_ADMIN_BOOTSTRAP=false
ADMIN_BOOTSTRAP_TOKEN=""

# 6. Restart application
```

### Password Hashing
- **Algorithm**: bcrypt with cost=12 (app/core/security.py)
- **Status**: ✅ Implemented via fastapi-users

```python
# From app/core/security.py:
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time bcrypt comparison via CryptContext."""
```

### Email Verification
- **Token Type**: Time-limited JWT (24-hour validity)
- **Purpose**: Email ownership verification before account activation
- **Route**: POST /api/v1/auth/verify-email

### Password Reset Flow
- **Token Type**: Time-limited JWT (15-minute validity)  
- **Route**: POST /api/v1/auth/request-password-reset
- **Validation**: Token includes user_id bound at creation time

### CORS Configuration
```env
# .env:
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:5173,...
CORS_ALLOW_CREDENTIALS=true  # Include cookies/auth headers
```

### Database Connection Security
- **Requirement**: PostgreSQL in production (SQLite allowed only in tests)
- **Validation**: (config/settings.py, lines 72-89)
- **Status**: ✅ Enforced at startup

### HTTPS/TLS
- **Status**: ⚠️ Application-agnostic (configured at deployment level)
- **Recommendation**: Use nginx/Kubernetes Ingress with TLS termination
- **Kubernetes**: See k8s/ingress.yaml for TLS setup

```yaml
# k8s/ingress.yaml:
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: tls-secret
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
```

## 🚨 Security Hardening Recommendations

### 1. Bootstrap Endpoint Validation (PRIORITY: HIGH)

**Current Status**: ✅ Already implemented with good checks

**Enhancements to Consider**:
- Add detailed audit logging of every bootstrap attempt
- Send email notification to admin configured email on success
- Implement exponential backoff after 3 failed attempts
- Store bootstrap metadata (IP, User-Agent, timestamp)

**Implementation**:
```python
# app/services/auth/audit_service.py (new)
def log_bootstrap_attempt(ip: str, token: str, success: bool, reason: Optional[str] = None):
    """Log bootstrap attempts for security audit trail."""
    # Store in BootstrapAuditLog table
```

### 2. Rate Limiting Enhancement (PRIORITY: MEDIUM)

**Current**: Redis-based, 3 requests/minute per endpoint
**Enhancement**: Implement sliding window per IP

```python
# app/middleware/rate_limiter_redis.py (enhancement):
# Track per-IP bootstrap attempts over 1 hour window
# Ban IP after 10 failed attempts in 1 hour
```

### 3. Secrets Validation on Startup (PRIORITY: HIGH)

**Recommendation**: Add validation that catches misconfig before runtime crashes

```python
# config/settings.py (enhancement):
@field_validator("ADMIN_BOOTSTRAP_TOKEN")
@classmethod
def validate_bootstrap_token(cls, value: str, info: ValidationInfo) -> str:
    allow_bootstrap = info.data.get("ALLOW_ADMIN_BOOTSTRAP", False)
    if allow_bootstrap and not value:
        raise ValueError(
            "ADMIN_BOOTSTRAP_TOKEN must be set when ALLOW_ADMIN_BOOTSTRAP=true"
        )
    return value.strip() if value else ""
```

### 4. File Encryption (PRIORITY: MEDIUM)

**Current**: Support exists for AES-256-GCM via ENCRYPTION_KEY
**Status**: ⚠️ Keys in settings but not fully integrated

**Affected Fields**:
- User phone numbers
- Payment method tokens
- PII sensitive data

**Implementation Path**:
```python
# app/core/encryption.py (already exists)
# Add automatic field encryption for sensitive User/PaymentMethod fields
```

### 5. Audit Logging (PRIORITY: MEDIUM)

**Recommended**: Log all sensitive operations:
- Login/logout, password changes
- Admin actions (user verification, role assignment)
- Payment processing, refunds
- Content modifications by privileged users

**Implementation**:
```python
# Create AdminActionLog model (partially exists in tests)
# Middleware to capture all requests to /admin routes
# Structured logging with correlation IDs
```

### 6. API Key Authentication (PRIORITY: LOW)

**Current**: Only JWT + OAuth2 Password flow
**Recommendation**: Add application API keys for service-to-service auth

```python
# app/models.py (addition):
class APIKey(Base):
    __tablename__ = "api_keys"
    user_id: GUID = Column(GUID, ForeignKey("user.id"))
    hashed_key: str = Column(String, unique=True)  # Bcrypt hashed
    name: str = Column(String)
    last_used: datetime = Column(DateTime)
```

### 7. Stripe Webhook Signature Verification (PRIORITY: HIGH)

**Current**: Implementation in app/services/billing/stripe_webhook_service.py
**Status**: ✅ Uses stripe.Webhook.construct_event() for validation

```python
# ✅ GOOD - Already implemented:
event = stripe.Webhook.construct_event(
    payload=payload,
    sig_header=stripe_signature,
    secret=settings.STRIPE_WEBHOOK_SECRET,
)
```

### 8. SQL Injection Prevention (PRIORITY: HIGH)

**Status**: ✅ Protected via SQLAlchemy ORM parameterized queries
**No raw SQL without parameterization** - audit with:
```bash
grep -r "execute(" app/ --include="*.py" | grep -v "execute(q" | grep -v "#"
```

### 9. CSRF Protection (PRIORITY: MEDIUM)

**Current**: ⚠️ Not explicitly implemented (SPA frontend assumes CORS origin validation)
**Status**: Application assumes SPA with no form-based requests

### 10. Content Security Policy (PRIORITY: LOW)

**Recommendation**: Add CSP headers for frontend protection

```python
# app/middleware/security_headers.py (new)
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

# app/main.py:
app.add_middleware(SecurityHeadersMiddleware)
```

## 📋 Security Deployment Checklist

- [ ] SECRET_KEY changed and >= 32 characters
- [ ] ALLOW_ADMIN_BOOTSTRAP=false in production
- [ ] ADMIN_BOOTSTRAP_TOKEN unset after bootstrap
- [ ] Database password rotated and secure
- [ ] JWT RSA keys generated and deployed
- [ ] HTTPS/TLS configured at ingress layer
- [ ] Redis password configured (if enabled)
- [ ] Stripe API keys in secure vault (not .env)
- [ ] OPENAI_API_KEY in secure vault (if used)
- [ ] SENTRY_DSN configured for error tracking
- [ ] Audit logging enabled
- [ ] Rate limiting thresholds appropriate for load
- [ ] Database backups scheduled
- [ ] Log retention policy defined

## 🔑 Key Generation Procedures

### Generate SECRET_KEY (32 bytes)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Generate ADMIN_BOOTSTRAP_TOKEN
```bash
openssl rand -hex 32
```

### Generate RSA Keys for RS256
```bash
python scripts/generate_rsa_keys.py
# Creates: jwt_private_key.pem, jwt_public_key.pem
```

### Generate ENCRYPTION_KEY (AES-256)
```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Produces 64-character hex string (32 bytes)
```

## 📚 Related Documentation

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Top 10](https://owasp.org/Top10/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Stripe Webhook Signing](https://stripe.com/docs/webhooks/signatures)

## 🤝 Contributing to Security

If you discover a security vulnerability, please:
1. Do NOT open a public issue
2. Email security@bizify.app with details
3. Include: Vulnerability description, reproduction steps, potential impact
4. Allow 48 hours for initial response
