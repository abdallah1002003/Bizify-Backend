# Rollback Strategy

This document outlines the procedures for reverting a failed deployment in the Bizify system.

## 1. Automated Rollback (CI/CD)

The current `cd.yml` workflow includes **Smoke Tests**. If a smoke test fails in the Staging or Production job, the deployment process will halt immediately.

### Action on Smoke Test Failure
- The job will mark as **FAILED** in GitHub Actions.
- No further steps (like creating a GitHub Release) will execute.
- **Manual Intervention Required:** Since `docker compose up -d` was already called, a manual rollback or fix is needed if the service is in a broken state.

## 2. Manual Rollback Procedures

### A. Revert to Previous Image Tag
If a deployment succeeds but reveals issues later:

1.  **Identify Last Stable Image:** Check GitHub Container Registry (GHCR) for the previous stable image tag (e.g., `v1.2.3` or a specific SHA).
2.  **Update Deployment Environment:**
    ```bash
    ssh username@host
    cd /opt/bizify
    # Edit docker-compose.yml or use env var to point to previous tag
    # Example:
    export IMAGE_TAG=v1.2.3
    docker compose pull
    docker compose up -d
    ```

### B. Database Rollback (Alembic)
If the deployment included a breaking schema migration:

1.  **Downgrade Schema:**
    ```bash
    docker compose exec api alembic downgrade -1  # Revert many-to-one
    # OR revert to specific head
    docker compose exec api alembic downgrade <previous_revision_id>
    ```
    > [!WARNING]
    > Schema downgrades may involve data loss if columns were deleted. Always prefer "Fix Forward" for data-critical changes.

## 3. Post-Rollback Verification
After any rollback, run the smoke tests manually from the server or a local environment:
```bash
python scripts/smoke_test.py https://bizify.app
```

## 4. Rollback Readiness Checklist
- [ ] Database backup taken before deployment (Standard operation).
- [ ] SSH access to servers verified.
- [ ] Previous image tags available in GHCR.
