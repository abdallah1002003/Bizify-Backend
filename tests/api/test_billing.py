from datetime import datetime, timezone

from fastapi.testclient import TestClient

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import SubscriptionStatus, UserRole


def test_create_and_read_plan(client: TestClient, db, auth_headers: dict, test_user):
    test_user.role = UserRole.ADMIN
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    payload = {
        "name": "Pro",
        "price": 20.0,
        "features_json": {"ai_runs": 100},
        "is_active": True,
    }

    create_res = client.post("/api/v1/plans/", json=payload, headers=auth_headers)
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["name"] == "Pro"

    list_res = client.get("/api/v1/plans/", headers=auth_headers)
    assert list_res.status_code == 200
    plans = list_res.json()
    assert any(plan["id"] == created["id"] for plan in plans)


def test_subscription_routes_are_user_scoped(client: TestClient, db, auth_headers: dict, test_user):
    plan = models.Plan(name="Starter", price=0.0, features_json={"ai_runs": 10}, is_active=True)
    db.add(plan)
    db.commit()
    db.refresh(plan)

    create_payload = {
        "user_id": str(test_user.id),
        "plan_id": str(plan.id),
        "status": "pending",
    }
    create_res = client.post("/api/v1/subscriptions/", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 200
    own_subscription = create_res.json()
    assert own_subscription["user_id"] == str(test_user.id)

    other_user = models.User(
        name="Other User",
        email="other-sub@example.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    other_subscription = models.Subscription(
        user_id=other_user.id,
        plan_id=plan.id,
        status=SubscriptionStatus.PENDING,
        start_date=datetime.now(timezone.utc),
    )
    db.add(other_subscription)
    db.commit()
    db.refresh(other_subscription)

    list_res = client.get("/api/v1/subscriptions/", headers=auth_headers)
    assert list_res.status_code == 200
    subscriptions = list_res.json()
    assert len(subscriptions) == 1
    assert subscriptions[0]["id"] == own_subscription["id"]

    forbidden_res = client.get(
        f"/api/v1/subscriptions/{other_subscription.id}",
        headers=auth_headers,
    )
    assert forbidden_res.status_code == 403
