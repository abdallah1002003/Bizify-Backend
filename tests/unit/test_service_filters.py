from uuid import uuid4

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import ChatRole, ChatSessionType, UserRole
from app.services.billing import billing_service
from app.services.chat import chat_service
from app.services.core import core_service
from config.settings import Settings


def _create_user(db, email: str):
    user = models.User(
        name=f"User {email}",
        email=email,
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_billing_get_subscriptions_filters_by_user(db):
    user_a = _create_user(db, f"a_{uuid4().hex[:8]}@example.com")
    user_b = _create_user(db, f"b_{uuid4().hex[:8]}@example.com")

    plan = models.Plan(name="Pro", price=20.0, features_json={"ai_runs": 100})
    db.add(plan)
    db.commit()
    db.refresh(plan)

    billing_service.create_subscription(db, {"user_id": user_a.id, "plan_id": plan.id})
    billing_service.create_subscription(db, {"user_id": user_b.id, "plan_id": plan.id})

    filtered = billing_service.get_subscriptions(db, user_id=user_a.id)
    assert len(filtered) == 1
    assert filtered[0].user_id == user_a.id

    all_subscriptions = billing_service.get_subscriptions(db)
    assert len(all_subscriptions) == 2


def test_chat_get_messages_filters_by_user(db):
    user_a = _create_user(db, f"chat_a_{uuid4().hex[:8]}@example.com")
    user_b = _create_user(db, f"chat_b_{uuid4().hex[:8]}@example.com")

    session_a = chat_service.create_chat_session(
        db,
        user_id=user_a.id,
        session_type=ChatSessionType.IDEA_CHAT,
    )
    session_b = chat_service.create_chat_session(
        db,
        user_id=user_b.id,
        session_type=ChatSessionType.GENERAL,
    )

    chat_service.add_message(db, session_id=session_a.id, role=ChatRole.USER, content="hello a")
    chat_service.add_message(db, session_id=session_a.id, role=ChatRole.AI, content="reply a")
    chat_service.add_message(db, session_id=session_b.id, role=ChatRole.USER, content="hello b")

    filtered = chat_service.get_chat_messages(db, user_id=user_a.id)
    assert len(filtered) == 2
    assert all(message.session_id == session_a.id for message in filtered)


def test_core_get_notifications_filters_by_user(db):
    user_a = _create_user(db, f"n_a_{uuid4().hex[:8]}@example.com")
    user_b = _create_user(db, f"n_b_{uuid4().hex[:8]}@example.com")

    core_service.create_notification(db, {"user_id": user_a.id, "title": "A", "message": "m1"})
    core_service.create_notification(db, {"user_id": user_b.id, "title": "B", "message": "m2"})

    filtered = core_service.get_notifications(db, user_id=user_a.id)
    assert len(filtered) == 1
    assert filtered[0].user_id == user_a.id


def test_settings_parses_cors_allowed_origins_list():
    parsed = Settings(CORS_ALLOWED_ORIGINS="http://a.com, http://b.com")
    assert parsed.cors_allowed_origins_list == ["http://a.com", "http://b.com"]

    fallback = Settings(CORS_ALLOWED_ORIGINS="   ")
    assert fallback.cors_allowed_origins_list == ["http://localhost:3000"]
