# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Created this `CHANGELOG.md` to track project history.
- Added `/metrics` endpoint security using `X-Metrics-Key` header and `METRICS_API_KEY` setting.
- Created `dev-requirements.txt` to separate development and testing tools (like pytest, mypy, ruff, locust) from the production image.

### Changed
- Migrated token management from unmaintained `python-jose` to modern `PyJWT`.
- Updated application description in `main.py` to correctly reflect the Enterprise capabilities (Billing, Ideas, Payments, Chat, Auth).
- Refined production `requirements.txt` by removing development dependencies and updating base library lists.

### Security
- The `/metrics` Prometheus exposition endpoint is no longer strictly public; it now enforces API key authentication to avoid unintended information disclosure.
