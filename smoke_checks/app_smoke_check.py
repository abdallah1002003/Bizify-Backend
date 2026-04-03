import os
import sys

# Force a local database for an isolated smoke check.
os.environ["DATABASE_URL"] = "sqlite:///./sql_app.db"

from fastapi.testclient import TestClient

from app.main import app


def main() -> int:
    client = TestClient(app)
    checks = [
        ("/", 200),
        ("/health", 200),
        ("/openapi.json", 200),
        ("/api/v1/guidance/stages", 200),
    ]

    failures: list[str] = []

    for path, expected_status in checks:
        response = client.get(path)
        if response.status_code != expected_status:
            failures.append(
                f"{path}: expected {expected_status}, got {response.status_code}"
            )
            continue
        print(f"PASS {path} -> {response.status_code}")

    if failures:
        print("SMOKE CHECK FAILED")
        for failure in failures:
            print(failure)
        return 1

    print("SMOKE CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
