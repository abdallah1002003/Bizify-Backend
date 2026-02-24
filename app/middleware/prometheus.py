from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import Counter, Histogram, Gauge
from fastapi import FastAPI
from typing import Any

# Custom Metrics
# 1. User registrations
USER_REGISTRATIONS = Counter(
    "user_registrations_total",
    "Total number of user registrations",
    ["role"]
)

# 2. AI Agent performance
AI_AGENT_RUN_DURATION = Histogram(
    "ai_agent_run_duration_seconds",
    "Time spent running AI agents",
    ["agent_type", "status"],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, float("inf"))
)

AI_AGENT_RUNS = Counter(
    "ai_agent_runs_total",
    "Total number of AI agent runs",
    ["agent_type", "status"]
)

# 3. Database operations (can be expanded to individual queries if needed)
DB_OPERATION_DURATION = Histogram(
    "db_operation_duration_seconds",
    "Time spent on database operations",
    ["operation_type"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, float("inf"))
)

# 4. Active chat sessions
ACTIVE_CHAT_SESSIONS = Gauge(
    "active_chat_sessions",
    "Number of currently active chat sessions"
)

def setup_prometheus(app: FastAPI) -> Instrumentator:
    """
    Configure and initialize Prometheus instrumentation for the FastAPI app.
    """
    import logging
    logger = logging.getLogger("prometheus")
    
    # Check if metrics should be enabled
    import os
    enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    
    if not enable_metrics:
        logger.info("Prometheus metrics disabled via ENABLE_METRICS env var")
        return None

    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,  # We handle this check manually above for more control
        should_instrument_requests_inprogress=True,
        excluded_handlers=[".*admin.*", "/metrics", "/health"],
    )

    # Add default metrics
    instrumentator.add(metrics.request_size())
    instrumentator.add(metrics.response_size())
    instrumentator.add(metrics.latency())
    instrumentator.add(metrics.combined_size())

    # Instrument the app
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    
    logger.info("Prometheus metrics initialized and exposed at /metrics")
    return instrumentator

# Helper functions to record metrics
def record_user_registration(role: str) -> None:
    USER_REGISTRATIONS.labels(role=role).inc()

def record_ai_agent_run(agent_type: str, status: str, duration: float) -> None:
    AI_AGENT_RUNS.labels(agent_type=agent_type, status=status).inc()
    AI_AGENT_RUN_DURATION.labels(agent_type=agent_type, status=status).observe(duration)

def record_db_operation(operation_type: str, duration: float) -> None:
    DB_OPERATION_DURATION.labels(operation_type=operation_type).observe(duration)
