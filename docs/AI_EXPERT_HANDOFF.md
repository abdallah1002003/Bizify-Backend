# AI Expert Handoff

Report date: 2026-02-22

## Current validated status

- `pytest -q`: **49 passed** (0 failed)
- `ruff check app tests main.py health_check.py`: **clean**
- `mypy app main.py`: **clean**
- `coverage report -m`: **61% total**

## What was stabilized before handoff

- Fixed blocking type/lint issues that were preventing clean QA gates.
- Resolved runtime import cycles in billing/user service packages.
- Added a safe fallback for `Vector` when `pgvector` is unavailable (offline/local environments).
- Kept API/service behavior unchanged while unblocking test execution and static checks.

## Important context for AI expert

- AI runtime is still hybrid/mock-first in several flows:
  - `app/services/ai/provider_runtime.py`
  - `app/services/ai/ai_service.py`
- Embedding persistence uses `Vector(1536)` with a JSON fallback type when `pgvector` is not installed.
- Existing docs may still contain optimistic production claims; rely on this file + current CI outputs.

## Recommended first tasks for expert

1. Replace mock agent responses with production-grade prompting/evaluation flow.
2. Move synchronous AI execution to background workers/queue.
3. Define strict validation/guardrails for model output contracts.
4. Improve test coverage around AI/billing service internals (current total is 61%).
