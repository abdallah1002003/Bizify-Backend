# syntax=docker/dockerfile:1
# =============================================================================
# Stage 1 — Builder: install Python dependencies into an isolated venv
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# System-level build deps (psycopg2 needs libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2 — Runtime: minimal image that only copies what is needed
# =============================================================================
FROM python:3.12-slim AS runtime

# Runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8001

# Run migrations then start the server.
# alembic upgrade head is idempotent — safe to run on every container start.
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2"]
