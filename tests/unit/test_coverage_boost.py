"""
Coverage boost tests: exercises scaffold CRUD routes that previously had zero
or low HTTP-level test coverage (notifications, chat, billing, plans,
subscriptions, token blacklisting, and repository pattern).

All tests use the shared conftest fixtures (client, auth_headers, test_user).
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.models as models
from app.models.enums import ChatSessionType


# ---------------------------------------------------------------------------
# Token Blacklist unit tests
# ---------------------------------------------------------------------------

class TestTokenBlacklist:
    """Unit tests for the JTI blacklist module."""

    def test_blacklist_and_check(self):
        from app.core.token_blacklist import blacklist_token, is_token_blacklisted
        jti = str(uuid.uuid4())
        assert not is_token_blacklisted(jti)
        blacklist_token(jti, ttl_seconds=60)
        assert is_token_blacklisted(jti)

    def test_expired_token_not_blacklisted(self):
        from app.core.token_blacklist import blacklist_token, is_token_blacklisted
        jti = str(uuid.uuid4())
        # TTL=0 means already expired — should not be stored
        blacklist_token(jti, ttl_seconds=0)
        assert not is_token_blacklisted(jti)

    def test_unknown_jti_not_blacklisted(self):
        from app.core.token_blacklist import is_token_blacklisted
        assert not is_token_blacklisted(str(uuid.uuid4()))

    def test_revoked_token_rejected_by_api(
        self, client: TestClient, test_user, auth_headers: dict
    ):
        """After blacklisting the JTI, the same access token must return 401."""
        import jwt as jwt
        from config.settings import settings
        from datetime import datetime, timezone
        from app.core.token_blacklist import blacklist_token

        token = auth_headers["Authorization"].split(" ", 1)[1]
        payload = jwt.decode(
            token, settings.jwt_verify_key, algorithms=[settings.jwt_algorithm]
        )
        jti = payload["jti"]
        exp = payload["exp"]
        remaining = int(exp - datetime.now(timezone.utc).timestamp())
        blacklist_token(jti, remaining)

        resp = client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Notification routes  (prefix: /api/v1/notifications)
# NotificationCreate requires user_id in body — route overrides it server-side
# but schema still validates it.  We pass a sentinel UUID and the route
# replaces it with current_user.id before persisting.
# ---------------------------------------------------------------------------

class TestNotificationRoutes:

    def _notif_payload(self, user_id: uuid.UUID) -> dict:
        return {
            "user_id": str(user_id),
            "title": "Hello",
            "message": "World",
            "is_read": False,
        }

    def test_list_notifications_empty(self, client: TestClient, auth_headers: dict, test_user):
        resp = client.get("/api/v1/notifications/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_and_read_notification(
        self, client: TestClient, auth_headers: dict, test_user
    ):
        resp = client.post(
            "/api/v1/notifications/",
            json=self._notif_payload(test_user.id),
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Hello"
        nid = data["id"]

        resp = client.get(f"/api/v1/notifications/{nid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == nid

    def test_update_notification(self, client: TestClient, auth_headers: dict, test_user):
        resp = client.post(
            "/api/v1/notifications/",
            json=self._notif_payload(test_user.id),
            headers=auth_headers,
        )
        nid = resp.json()["id"]
        resp = client.put(
            f"/api/v1/notifications/{nid}",
            json={"is_read": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    def test_delete_notification(self, client: TestClient, auth_headers: dict, test_user):
        resp = client.post(
            "/api/v1/notifications/",
            json=self._notif_payload(test_user.id),
            headers=auth_headers,
        )
        nid = resp.json()["id"]
        resp = client.delete(f"/api/v1/notifications/{nid}", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_notification_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get(f"/api/v1/notifications/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_notification_access_denied(
        self,
        client: TestClient,
        auth_headers: dict,
        another_user: models.User,
        db: Session,
    ):
        """User A cannot read User B's notification."""
        notif = models.Notification(
            user_id=another_user.id, title="Private", message="No", is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        resp = client.get(f"/api/v1/notifications/{notif.id}", headers=auth_headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Chat session routes  (prefix: /api/v1/chat_sessions)
# ChatSessionCreate requires user_id in body — route replaces it server-side.
# ---------------------------------------------------------------------------

class TestChatSessionRoutes:

    def _session_payload(self, user_id: uuid.UUID) -> dict:
        return {
            "user_id": str(user_id),
            "session_type": ChatSessionType.GENERAL.value,
        }

    def test_list_chat_sessions_empty(self, client: TestClient, auth_headers: dict, test_user):
        resp = client.get("/api/v1/chat_sessions/", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_and_get_session(
        self, client: TestClient, auth_headers: dict, test_user
    ):
        resp = client.post(
            "/api/v1/chat_sessions/",
            json=self._session_payload(test_user.id),
            headers=auth_headers,
        )
        print("DEBUG RESP:", resp.json())
        assert resp.status_code == 200, resp.text
        sid = resp.json()["id"]

        resp = client.get(f"/api/v1/chat_sessions/{sid}", headers=auth_headers)
        assert resp.status_code == 200

    def test_update_session(self, client: TestClient, auth_headers: dict, test_user):
        resp = client.post(
            "/api/v1/chat_sessions/",
            json=self._session_payload(test_user.id),
            headers=auth_headers,
        )
        print("DEBUG UPDATE BEFORE:", resp.json())
        sid = resp.json()["id"]
        resp = client.put(
            f"/api/v1/chat_sessions/{sid}",
            json={"session_type": ChatSessionType.IDEA_CHAT.value},
            headers=auth_headers,
        )
        print("DEBUG UPDATE AFTER:", resp.json())
        assert resp.status_code == 200, resp.text

    def test_delete_session(self, client: TestClient, auth_headers: dict, test_user):
        resp = client.post(
            "/api/v1/chat_sessions/",
            json=self._session_payload(test_user.id),
            headers=auth_headers,
        )
        print("DEBUG DELETE BEFORE:", resp.json())
        sid = resp.json()["id"]
        resp = client.delete(f"/api/v1/chat_sessions/{sid}", headers=auth_headers)
        print("DEBUG DELETE AFTER:", resp.json())
        assert resp.status_code == 200, resp.text

    def test_session_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get(f"/api/v1/chat_sessions/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Plan routes  (prefix: /api/v1/plans)
# Plan model fields: name, price, features_json, is_active  (no description)
# ---------------------------------------------------------------------------

class TestPlanRoutes:

    def _make_admin_headers(self, db: Session, test_user: models.User) -> dict:
        from app.models.enums import UserRole
        from app.core.security import create_access_token
        test_user.role = UserRole.ADMIN
        db.add(test_user)
        db.commit()
        return {"Authorization": f"Bearer {create_access_token(subject=str(test_user.id))}"}

    def test_list_plans(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/plans/", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_plan_as_admin(
        self, client: TestClient, test_user: models.User, db: Session
    ):
        headers = self._make_admin_headers(db, test_user)
        payload = {"name": "Pro Plan", "price": 29.99, "features_json": {}, "is_active": True}
        resp = client.post("/api/v1/plans/", json=payload, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Pro Plan"

    def test_create_plan_as_non_admin_forbidden(
        self, client: TestClient, auth_headers: dict
    ):
        payload = {"name": "Free Plan", "price": 0.0, "features_json": {}, "is_active": True}
        resp = client.post("/api/v1/plans/", json=payload, headers=auth_headers)
        assert resp.status_code == 403

    def test_get_plan_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get(f"/api/v1/plans/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_read_plan_by_id(
        self, client: TestClient, test_user: models.User, db: Session
    ):
        headers = self._make_admin_headers(db, test_user)
        payload = {"name": "Starter", "price": 9.99, "features_json": {}, "is_active": True}
        created = client.post("/api/v1/plans/", json=payload, headers=headers).json()
        pid = created["id"]

        resp = client.get(f"/api/v1/plans/{pid}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == pid


# ---------------------------------------------------------------------------
# Subscription routes  (prefix: /api/v1/subscriptions)
# SubscriptionCreate: user_id (route sets from current_user), plan_id, status
# ---------------------------------------------------------------------------

class TestSubscriptionRoutes:

    def _create_plan(self, db: Session) -> models.Plan:
        plan = models.Plan(name="Basic", price=9.99, features_json={}, is_active=True)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    def test_list_subscriptions_empty(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/subscriptions/", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_and_get_subscription(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: models.User
    ):
        plan = self._create_plan(db)
        payload = {
            "user_id": str(test_user.id),
            "plan_id": str(plan.id),
            "status": "pending",
        }
        resp = client.post("/api/v1/subscriptions/", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        sid = resp.json()["id"]

        resp = client.get(f"/api/v1/subscriptions/{sid}", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_subscription_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get(f"/api/v1/subscriptions/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_subscription(
        self, client: TestClient, auth_headers: dict, db: Session, test_user: models.User
    ):
        plan = self._create_plan(db)
        payload = {
            "user_id": str(test_user.id),
            "plan_id": str(plan.id),
            "status": "pending",
        }
        resp = client.post("/api/v1/subscriptions/", json=payload, headers=auth_headers)
        sid = resp.json()["id"]
        resp = client.delete(f"/api/v1/subscriptions/{sid}", headers=auth_headers)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Repository Pattern — GenericRepository unit tests
# ---------------------------------------------------------------------------

class TestGenericRepository:

    def test_create_and_get(self, db: Session, test_user: models.User):
        from app.repositories.base_repository import GenericRepository
        repo = GenericRepository(db, models.Notification)
        obj = repo.create(
            {"user_id": test_user.id, "title": "Test", "message": "Msg", "is_read": False}
        )
        assert obj.id is not None
        fetched = repo.get(obj.id)
        assert fetched is not None
        assert fetched.title == "Test"

    def test_get_all(self, db: Session, test_user: models.User):
        from app.repositories.base_repository import GenericRepository
        repo = GenericRepository(db, models.Notification)
        repo.create({"user_id": test_user.id, "title": "A", "message": "M", "is_read": False})
        repo.create({"user_id": test_user.id, "title": "B", "message": "M", "is_read": False})
        results = repo.get_all(skip=0, limit=10)
        assert len(results) >= 2

    def test_update_with_dict(self, db: Session, test_user: models.User):
        from app.repositories.base_repository import GenericRepository
        repo = GenericRepository(db, models.Notification)
        obj = repo.create(
            {"user_id": test_user.id, "title": "Before", "message": "M", "is_read": False}
        )
        updated = repo.update(obj, {"title": "After"})
        assert updated.title == "After"

    def test_delete(self, db: Session, test_user: models.User):
        from app.repositories.base_repository import GenericRepository
        repo = GenericRepository(db, models.Notification)
        obj = repo.create(
            {"user_id": test_user.id, "title": "ToDelete", "message": "M", "is_read": False}
        )
        deleted = repo.delete(obj.id)
        assert deleted is not None
        assert repo.get(obj.id) is None

    def test_delete_nonexistent(self, db: Session):
        from app.repositories.base_repository import GenericRepository
        repo = GenericRepository(db, models.Notification)
        result = repo.delete(uuid.uuid4())
        assert result is None

    def test_count(self, db: Session, test_user: models.User):
        from app.repositories.base_repository import GenericRepository
        repo = GenericRepository(db, models.Notification)
        before = repo.count()
        repo.create(
            {"user_id": test_user.id, "title": "Count Me", "message": "M", "is_read": False}
        )
        assert repo.count() == before + 1

    def test_get_nonexistent(self, db: Session):
        from app.repositories.base_repository import GenericRepository
        repo = GenericRepository(db, models.Notification)
        result = repo.get(uuid.uuid4())
        assert result is None
