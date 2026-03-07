import pytest
from uuid import uuid4

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import ChatRole, ChatSessionType, UserRole
from app.services.billing.subscription_service import SubscriptionService
from app.services.chat.chat_service import ChatService
from app.services.core.core_service import CoreService
from config.settings import Settings


async def _create_user(async_db, email: str):
    user = models.User(
        name=f"User {email}",
        email=email,
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_billing_get_subscriptions_filters_by_user(async_db):
    user_a = await _create_user(async_db, f"a_{uuid4().hex[:8]}@example.com")
    user_b = await _create_user(async_db, f"b_{uuid4().hex[:8]}@example.com")

    plan = models.Plan(name="Pro", price=20.0, features_json={"ai_runs": 100})
    async_db.add(plan)
    await async_db.commit()
    await async_db.refresh(plan)

    service = SubscriptionService(async_db)
    await service.create_subscription({"user_id": user_a.id, "plan_id": plan.id})
    await service.create_subscription({"user_id": user_b.id, "plan_id": plan.id})

    filtered = await service.get_subscriptions(user_id=user_a.id)
    assert len(filtered) == 1
    assert filtered[0].user_id == user_a.id

    all_subscriptions = await service.get_subscriptions()
    assert len(all_subscriptions) == 2


@pytest.mark.asyncio
async def test_chat_get_messages_filters_by_user(async_db):
    user_a = await _create_user(async_db, f"chat_a_{uuid4().hex[:8]}@example.com")
    user_b = await _create_user(async_db, f"chat_b_{uuid4().hex[:8]}@example.com")

    service = ChatService(async_db)
    session_a = await service.create_chat_session(
        user_id=user_a.id,
        session_type=ChatSessionType.IDEA_CHAT,
    )
    session_b = await service.create_chat_session(
        user_id=user_b.id,
        session_type=ChatSessionType.GENERAL,
    )

    await service.add_message(session_id=session_a.id, role=ChatRole.USER, content="hello a")
    await service.add_message(session_id=session_a.id, role=ChatRole.AI, content="reply a")
    await service.add_message(session_id=session_b.id, role=ChatRole.USER, content="hello b")

    filtered = await service.get_chat_messages(user_id=user_a.id)
    assert len(filtered) == 2
    assert all(message.session_id == session_a.id for message in filtered)


@pytest.mark.asyncio
async def test_core_get_notifications_filters_by_user(async_db):
    user_a = await _create_user(async_db, f"n_a_{uuid4().hex[:8]}@example.com")
    user_b = await _create_user(async_db, f"n_b_{uuid4().hex[:8]}@example.com")

    service = CoreService(async_db)
    await service.create_notification({"user_id": user_a.id, "title": "A", "message": "m1"})
    await service.create_notification({"user_id": user_b.id, "title": "B", "message": "m2"})

    filtered = await service.get_notifications(user_id=user_a.id)
    assert len(filtered) == 1
    assert filtered[0].user_id == user_a.id


def test_settings_parses_cors_allowed_origins_list():
    parsed = Settings(CORS_ALLOWED_ORIGINS="http://a.com, http://b.com")
    assert parsed.cors_allowed_origins_list == ["http://a.com", "http://b.com"]

    fallback = Settings(CORS_ALLOWED_ORIGINS="   ")
    assert fallback.cors_allowed_origins_list == ["http://localhost:3000"]
