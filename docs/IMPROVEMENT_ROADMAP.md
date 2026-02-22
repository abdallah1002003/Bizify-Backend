# Improvement Roadmap

Date: 2026-02-22

## Phase 1 - Stabilize (1-2 weeks)

- Finalize legacy service import cleanup.
- Enforce non-default `SECRET_KEY` in production startup checks.
- Verify all critical routes have explicit ownership/admin authorization tests.
- Align README setup steps with required env variables.

## Phase 2 - Reliability (2-4 weeks)

- Introduce structured logging with request correlation IDs.
- Add service-level metrics (latency, error rate, DB retries).
- Add dashboards/alerts for auth errors, rate-limit spikes, and 5xx rates.
- Expand integration tests for end-to-end business workflows.

## Phase 3 - Scale (4-8 weeks)

- Add caching strategy for high-read endpoints (Redis where needed).
- Review async adoption opportunities in IO-heavy paths.
- Benchmark and tune DB pool settings under realistic load.
- Define API versioning and deprecation policy for future changes.

## Phase 4 - Governance (ongoing)

- Add security checklist to PR template.
- Track test coverage trend in CI.
- Schedule periodic dependency updates and vulnerability scans.
- Keep route documentation updated with every new endpoint.

## Success Criteria

- Zero legacy imports in app/test code.
- Production environments reject weak/default secrets.
- Alerting in place for critical reliability signals.
- Documentation stays in sync with route additions/removals.
