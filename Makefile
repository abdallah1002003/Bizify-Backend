.PHONY: help dev-up dev-down dev-logs install migrate test test-cov lint clean redis-profile

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
help:
	@echo ""
	@echo "Bizify Backend – Developer Commands"
	@echo "======================================"
	@echo "  make install       Install Python dependencies into venv"
	@echo "  make dev-up        Start local infrastructure (Postgres + Redis)"
	@echo "  make dev-down      Stop local infrastructure"
	@echo "  make dev-logs      Tail local infrastructure logs"
	@echo "  make migrate       Run Alembic migrations (upgrade head)"
	@echo "  make test          Run unit test suite"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make redis-profile Run async Redis load profile"
	@echo "  make lint          Run ruff linter"
	@echo "  make clean         Remove .pyc files and __pycache__ dirs"
	@echo ""

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
VENV     := venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
PYTEST   := $(VENV)/bin/pytest
ALEMBIC  := $(VENV)/bin/alembic

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅  Dependencies installed"

# ---------------------------------------------------------------------------
# Local Infrastructure (Postgres + Redis only – no API container)
# ---------------------------------------------------------------------------
dev-up:
	docker compose -f docker-compose.dev.yml up -d
	@echo "✅  Local infrastructure started (Postgres + Redis)"

dev-down:
	docker compose -f docker-compose.dev.yml down
	@echo "✅  Local infrastructure stopped"

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
migrate:
	$(ALEMBIC) upgrade head
	@echo "✅  Migrations applied"

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
test:
	$(PYTEST) tests/unit/ -v

test-cov:
	$(PYTEST) tests/unit/ -v --cov=app --cov-report=term-missing

redis-profile:
	$(PYTHON) scripts/redis_async_load_test.py \
		--host $${REDIS_HOST:-localhost} \
		--port $${REDIS_PORT:-6379} \
		--db $${REDIS_DB:-0} \
		--concurrency $${REDIS_LOAD_CONCURRENCY:-100} \
		--operations $${REDIS_LOAD_OPERATIONS:-50000} \
		--read-ratio $${REDIS_LOAD_READ_RATIO:-0.8} \
		--keyspace $${REDIS_LOAD_KEYSPACE:-10000} \
		--value-size $${REDIS_LOAD_VALUE_SIZE:-512} \
		--ttl-seconds $${REDIS_LOAD_TTL_SECONDS:-300} \
		--warmup-operations $${REDIS_LOAD_WARMUP_OPERATIONS:-5000}

# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------
lint:
	$(VENV)/bin/ruff check app/ tests/ --fix

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅  Cleaned up .pyc and __pycache__"
