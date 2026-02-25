# type: ignore
"""
Prometheus metrics for monitoring Bizify API.

Tracks:
- Request count and duration
- Database query performance
- Cache hit/miss rates
- Authentication events
- Business logic counters
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional
import time

# Create a custom registry
REGISTRY = CollectorRegistry()

# ============================================================================
# HTTP Request Metrics
# ============================================================================

http_requests_total = Counter(
    "bizify_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=REGISTRY,
)

http_request_duration_seconds = Histogram(
    "bizify_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)

# ============================================================================
# Database Metrics
# ============================================================================

db_query_duration_seconds = Histogram(
    "bizify_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=REGISTRY,
)

db_query_errors_total = Counter(
    "bizify_db_query_errors_total",
    "Total database query errors",
    ["operation", "table", "error_type"],
    registry=REGISTRY,
)

db_connections_active = Gauge(
    "bizify_db_connections_active",
    "Number of active database connections",
    registry=REGISTRY,
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_hits_total = Counter(
    "bizify_cache_hits_total",
    "Total cache hits",
    ["cache_backend"],
    registry=REGISTRY,
)

cache_misses_total = Counter(
    "bizify_cache_misses_total",
    "Total cache misses",
    ["cache_backend"],
    registry=REGISTRY,
)

cache_size_bytes = Gauge(
    "bizify_cache_size_bytes",
    "Cache size in bytes",
    ["cache_backend"],
    registry=REGISTRY,
)

# ============================================================================
# Authentication Metrics
# ============================================================================

auth_attempts_total = Counter(
    "bizify_auth_attempts_total",
    "Total authentication attempts",
    ["method", "success"],
    registry=REGISTRY,
)

auth_tokens_issued_total = Counter(
    "bizify_auth_tokens_issued_total",
    "Total tokens issued",
    ["token_type"],
    registry=REGISTRY,
)

active_sessions = Gauge(
    "bizify_active_sessions",
    "Number of active user sessions",
    registry=REGISTRY,
)

# ============================================================================
# Business Logic Metrics
# ============================================================================

ideas_created_total = Counter(
    "bizify_ideas_created_total",
    "Total ideas created",
    registry=REGISTRY,
)

businesses_created_total = Counter(
    "bizify_businesses_created_total",
    "Total businesses created",
    registry=REGISTRY,
)

chat_messages_total = Counter(
    "bizify_chat_messages_total",
    "Total chat messages",
    ["role"],
    registry=REGISTRY,
)

users_active = Gauge(
    "bizify_users_active",
    "Number of active users",
    registry=REGISTRY,
)

subscriptions_active = Gauge(
    "bizify_subscriptions_active",
    "Number of active subscriptions",
    registry=REGISTRY,
)

# ============================================================================
# AI Service Metrics
# ============================================================================

ai_requests_total = Counter(
    "bizify_ai_requests_total",
    "Total AI service requests",
    ["provider", "model", "status"],
    registry=REGISTRY,
)

ai_request_duration_seconds = Histogram(
    "bizify_ai_request_duration_seconds",
    "AI request duration in seconds",
    ["provider", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=REGISTRY,
)

ai_tokens_used_total = Counter(
    "bizify_ai_tokens_used_total",
    "Total AI tokens used",
    ["provider", "model", "token_type"],
    registry=REGISTRY,
)

# ============================================================================
# Email Service Metrics
# ============================================================================

emails_sent_total = Counter(
    "bizify_emails_sent_total",
    "Total emails sent",
    ["template", "status"],
    registry=REGISTRY,
)

email_send_duration_seconds = Histogram(
    "bizify_email_send_duration_seconds",
    "Email send duration in seconds",
    ["template"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
    registry=REGISTRY,
)

# ============================================================================
# Error Metrics
# ============================================================================

errors_total = Counter(
    "bizify_errors_total",
    "Total errors by type",
    ["error_type", "service"],
    registry=REGISTRY,
)

validation_errors_total = Counter(
    "bizify_validation_errors_total",
    "Total validation errors",
    ["field", "error_code"],
    registry=REGISTRY,
)

# ============================================================================
# Business Rate Metrics
# ============================================================================

rate_limit_exceeded_total = Counter(
    "bizify_rate_limit_exceeded_total",
    "Total rate limit exceeded events",
    ["user_id"],
    registry=REGISTRY,
)

requests_per_minute = Gauge(
    "bizify_requests_per_minute",
    "Requests per minute by user",
    ["user_id"],
    registry=REGISTRY,
)


# ============================================================================
# Helper Functions
# ============================================================================

class MetricsTimer:
    """Context manager for timing operations and recording metrics."""

    def __init__(self, histogram: Histogram, labels: dict):
        """
        Initialize timer for metric recording.

        Args:
            histogram: Prometheus histogram to record to
            labels: Labels for the metric
        """
        self.histogram = histogram
        self.labels = labels
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Record metric."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.histogram.labels(**self.labels).observe(duration)


def record_http_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics."""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_db_query(operation: str, table: str, duration: float, error: bool = False):
    """Record database query metrics."""
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)
    if error:
        db_query_errors_total.labels(
            operation=operation, table=table, error_type="query_error"
        ).inc()


def record_cache_operation(backend: str, hit: bool):
    """Record cache operation."""
    if hit:
        cache_hits_total.labels(cache_backend=backend).inc()
    else:
        cache_misses_total.labels(cache_backend=backend).inc()


def record_auth_attempt(method: str, success: bool):
    """Record authentication attempt."""
    auth_attempts_total.labels(method=method, success=str(success)).inc()


def record_ai_request(provider: str, model: str, duration: float, success: bool):
    """Record AI service request."""
    status = "success" if success else "error"
    ai_requests_total.labels(provider=provider, model=model, status=status).inc()
    ai_request_duration_seconds.labels(provider=provider, model=model).observe(duration)


def record_email_sent(template: str, success: bool):
    """Record sent email."""
    status = "success" if success else "error"
    emails_sent_total.labels(template=template, status=status).inc()


def record_error(error_type: str, service: str):
    """Record error occurrence."""
    errors_total.labels(error_type=error_type, service=service).inc()
