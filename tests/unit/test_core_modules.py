"""
Tests for core modules:
  - app/core/exceptions.py      (AppException hierarchy + http_exception_from_app_exception)
  - app/core/security.py        (JWT creation/verification, password hashing)
  - app/core/token_blacklist.py (blacklist_token / is_token_blacklisted)
  - app/repositories/base_repository.py (GenericRepository CRUD)
"""
import time
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.core.exceptions import (
    AccessDeniedError,
    AppException,
    ConflictError,
    DatabaseError,
    ExternalServiceError,
    InvalidStateError,
    ResourceNotFoundError,
    ValidationError,
    http_exception_from_app_exception,
)
from app.core import security, token_blacklist


# ===========================================================================
# exceptions.py
# ===========================================================================

class TestAppException:
    def test_defaults(self):
        exc = AppException("Something broke")
        assert exc.message == "Something broke"
        assert exc.code == "INTERNAL_ERROR"
        assert exc.details == {}
        assert exc.status_code == 500
        assert str(exc) == "Something broke"

    def test_custom_code_and_details(self):
        exc = AppException("msg", code="MY_CODE", details={"k": "v"}, status_code=503)
        assert exc.code == "MY_CODE"
        assert exc.details == {"k": "v"}
        assert exc.status_code == 503


class TestValidationError:
    def test_basic(self):
        exc = ValidationError("bad input")
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.details == {}

    def test_with_field(self):
        exc = ValidationError("bad input", field="email")
        assert exc.details["field"] == "email"

    def test_with_field_and_details(self):
        exc = ValidationError("bad", field="name", details={"reason": "too short"})
        assert exc.details["field"] == "name"
        assert exc.details["reason"] == "too short"


class TestResourceNotFoundError:
    def test_message_format(self):
        exc = ResourceNotFoundError("User", "abc-123")
        assert "User" in exc.message
        assert "abc-123" in exc.message
        assert exc.code == "NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_details(self):
        exc = ResourceNotFoundError("Plan", "xyz")
        assert exc.details["resource_type"] == "Plan"
        assert exc.details["resource_id"] == "xyz"

    def test_extra_details(self):
        exc = ResourceNotFoundError("User", "1", details={"extra": "info"})
        assert exc.details["extra"] == "info"


class TestAccessDeniedError:
    def test_without_resource(self):
        exc = AccessDeniedError("delete")
        assert "delete" in exc.message
        assert exc.code == "ACCESS_DENIED"
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_with_resource(self):
        exc = AccessDeniedError("update", resource_type="Subscription")
        assert "Subscription" in exc.message
        assert exc.details["resource_type"] == "Subscription"

    def test_with_details(self):
        exc = AccessDeniedError("view", details={"reason": "not owner"})
        assert exc.details["reason"] == "not owner"


class TestConflictError:
    def test_basic(self):
        exc = ConflictError("email already exists")
        assert exc.code == "CONFLICT"
        assert exc.status_code == status.HTTP_409_CONFLICT

    def test_conflict_field(self):
        exc = ConflictError("dup", conflict_field="email", existing_value="a@b.com")
        assert exc.details["conflict_field"] == "email"
        assert exc.details["existing_value"] == "a@b.com"

    def test_no_existing_value(self):
        exc = ConflictError("dup", conflict_field="email")
        assert "conflict_field" in exc.details
        assert "existing_value" not in exc.details


class TestExternalServiceError:
    def test_without_original_error(self):
        exc = ExternalServiceError("Stripe", "create_charge")
        assert "Stripe" in exc.message
        assert "create_charge" in exc.message
        assert exc.code == "EXTERNAL_SERVICE_ERROR"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY

    def test_with_original_error(self):
        exc = ExternalServiceError("OpenAI", "completion", original_error="Rate limited")
        assert "Rate limited" in exc.message
        assert exc.details["external_error"] == "Rate limited"

    def test_details_populated(self):
        exc = ExternalServiceError("Stripe", "refund")
        assert exc.details["service"] == "Stripe"
        assert exc.details["operation"] == "refund"


class TestDatabaseError:
    def test_without_entity(self):
        exc = DatabaseError("create")
        assert "create" in exc.message
        assert exc.code == "DATABASE_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_with_entity(self):
        exc = DatabaseError("update", entity_type="User")
        assert "User" in exc.message

    def test_with_original_error(self):
        exc = DatabaseError("delete", original_error="FK violation")
        assert "FK violation" in exc.message

    def test_details(self):
        exc = DatabaseError("create", entity_type="Idea", original_error="null constraint")
        assert exc.details["operation"] == "create"
        assert exc.details["entity_type"] == "Idea"
        assert exc.details["db_error"] == "null constraint"


class TestInvalidStateError:
    def test_basic(self):
        exc = InvalidStateError("cannot cancel")
        assert exc.code == "INVALID_STATE"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_with_states(self):
        exc = InvalidStateError("bad op", current_state="active", required_state="inactive")
        assert exc.details["current_state"] == "active"
        assert exc.details["required_state"] == "inactive"

    def test_no_states(self):
        exc = InvalidStateError("bad op")
        assert "current_state" not in exc.details
        assert "required_state" not in exc.details


class TestHttpExceptionFromAppException:
    def test_converts_correctly(self):
        app_exc = ResourceNotFoundError("User", "99")
        http_exc = http_exception_from_app_exception(app_exc)
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == status.HTTP_404_NOT_FOUND
        assert http_exc.detail["error"] == "NOT_FOUND"
        assert http_exc.detail["message"] == app_exc.message
        assert http_exc.detail["details"] == app_exc.details

    def test_validation_error_conversion(self):
        app_exc = ValidationError("bad", field="name")
        http_exc = http_exception_from_app_exception(app_exc)
        assert http_exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ===========================================================================
# security.py
# ===========================================================================

class TestPasswordSecurity:
    def test_hash_and_verify(self):
        pw = "SuperSecret123!"
        hashed = security.get_password_hash(pw)
        assert hashed != pw
        assert security.verify_password(pw, hashed)

    def test_wrong_password(self):
        hashed = security.get_password_hash("correct")
        assert not security.verify_password("wrong", hashed)

    def test_different_hashes_same_password(self):
        pw = "same_password"
        h1 = security.get_password_hash(pw)
        h2 = security.get_password_hash(pw)
        assert h1 != h2  # bcrypt salts differ
        assert security.verify_password(pw, h1)
        assert security.verify_password(pw, h2)


class TestJWTTokens:
    def test_access_token_created(self):
        token = security.create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_access_token_with_custom_expiry(self):
        token = security.create_access_token("user-abc", expires_delta=timedelta(minutes=5))
        assert isinstance(token, str)

    def test_refresh_token_created(self):
        token = security.create_refresh_token("user-123")
        assert isinstance(token, str)

    def test_refresh_token_with_custom_expiry(self):
        token = security.create_refresh_token("user-abc", expires_delta=timedelta(days=1))
        assert isinstance(token, str)


class TestPasswordResetToken:
    def test_create_and_verify(self):
        token = security.create_password_reset_token("user@test.com")
        payload = security.verify_password_reset_token(token)
        assert payload is not None
        assert payload["sub"] == "user@test.com"
        assert payload["type"] == "password_reset"

    def test_invalid_token(self):
        result = security.verify_password_reset_token("invalid.jwt.token")
        assert result is None

    def test_wrong_type_rejected(self):
        # access token should not pass password_reset verify
        token = security.create_access_token("user@test.com")
        result = security.verify_password_reset_token(token)
        assert result is None


class TestEmailVerificationToken:
    def test_create_and_verify(self):
        token = security.create_email_verification_token("verify@test.com")
        payload = security.verify_email_verification_token(token)
        assert payload is not None
        assert payload["sub"] == "verify@test.com"
        assert payload["type"] == "email_verification"

    def test_invalid_token(self):
        result = security.verify_email_verification_token("not.a.token")
        assert result is None

    def test_wrong_type_rejected(self):
        token = security.create_access_token("verify@test.com")
        result = security.verify_email_verification_token(token)
        assert result is None


# ===========================================================================
# token_blacklist.py (tests always use in-memory since APP_ENV=test)
# ===========================================================================

class TestTokenBlacklist:
    def setup_method(self):
        """Clear the in-memory store before each test."""
        token_blacklist._memory_store.clear()

    def test_blacklist_and_check(self):
        jti = str(uuid.uuid4())
        token_blacklist.blacklist_token(jti, ttl_seconds=60)
        assert token_blacklist.is_token_blacklisted(jti)

    def test_non_blacklisted_jti(self):
        jti = str(uuid.uuid4())
        assert not token_blacklist.is_token_blacklisted(jti)

    def test_already_expired_ttl_is_skipped(self):
        jti = str(uuid.uuid4())
        token_blacklist.blacklist_token(jti, ttl_seconds=0)
        # ttl=0 means expired — should NOT be stored
        assert not token_blacklist.is_token_blacklisted(jti)

    def test_negative_ttl_is_skipped(self):
        jti = str(uuid.uuid4())
        token_blacklist.blacklist_token(jti, ttl_seconds=-1)
        assert not token_blacklist.is_token_blacklisted(jti)

    def test_lazy_cleanup_on_write(self):
        # Insert an already-expired entry manually
        old_jti = str(uuid.uuid4())
        token_blacklist._memory_store[old_jti] = time.time() - 10  # expired 10s ago
        # Insert a new valid entry — this should trigger cleanup
        new_jti = str(uuid.uuid4())
        token_blacklist.blacklist_token(new_jti, ttl_seconds=60)
        # Expired entry should be gone
        assert old_jti not in token_blacklist._memory_store
        # New entry should be here
        assert token_blacklist.is_token_blacklisted(new_jti)

    def test_read_expired_entry_returns_false(self):
        jti = str(uuid.uuid4())
        # Set expiry in the past
        token_blacklist._memory_store[jti] = time.time() - 1
        assert not token_blacklist.is_token_blacklisted(jti)
        # Should also have been cleaned up
        assert jti not in token_blacklist._memory_store


# ===========================================================================
# base_repository.py
# ===========================================================================

class TestGenericRepository:
    """Tests using a mock SQLAlchemy session — no database required."""

    def _make_repo(self):
        from app.repositories.base_repository import GenericRepository

        class FakeModel:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        mock_db = MagicMock()
        repo = GenericRepository(mock_db, FakeModel)
        return repo, mock_db, FakeModel

    def test_get(self):
        repo, mock_db, FakeModel = self._make_repo()
        fake_obj = FakeModel(id=1, name="test")
        mock_db.get.return_value = fake_obj
        result = repo.get(1)
        mock_db.get.assert_called_once_with(FakeModel, 1)
        assert result == fake_obj

    def test_get_not_found(self):
        repo, mock_db, FakeModel = self._make_repo()
        mock_db.get.return_value = None
        result = repo.get(999)
        assert result is None

    def test_get_all(self):
        repo, mock_db, FakeModel = self._make_repo()
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
            FakeModel(id=1), FakeModel(id=2)
        ]
        results = repo.get_all(skip=0, limit=10)
        assert len(results) == 2

    def test_count(self):
        repo, mock_db, FakeModel = self._make_repo()
        mock_db.query.return_value.count.return_value = 42
        assert repo.count() == 42

    def test_create(self):
        repo, mock_db, FakeModel = self._make_repo()
        mock_db.refresh = MagicMock()
        result = repo.create({"name": "new_item", "value": 10})
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_with_dict(self):
        repo, mock_db, FakeModel = self._make_repo()
        obj = FakeModel(name="old", value=1)
        mock_db.refresh = MagicMock()
        repo.update(obj, {"name": "new"})
        assert obj.name == "new"
        mock_db.commit.assert_called_once()

    def test_update_with_pydantic_model(self):
        repo, mock_db, FakeModel = self._make_repo()
        obj = FakeModel(name="old")
        mock_db.refresh = MagicMock()

        pydantic_update = MagicMock()
        pydantic_update.model_dump.return_value = {"name": "new_pydantic"}

        repo.update(obj, pydantic_update)
        assert obj.name == "new_pydantic"

    def test_update_with_legacy_dict_method(self):
        repo, mock_db, FakeModel = self._make_repo()
        obj = FakeModel(name="old")
        mock_db.refresh = MagicMock()

        # Simulate an object with a .dict() method (Pydantic v1 style)
        legacy_pydantic = MagicMock()
        del legacy_pydantic.model_dump  # no model_dump attribute
        legacy_pydantic.dict.return_value = {"name": "from_dict_method"}

        repo.update(obj, legacy_pydantic)
        assert obj.name == "from_dict_method"


    def test_update_skips_none_values(self):
        repo, mock_db, FakeModel = self._make_repo()
        obj = FakeModel(name="keep")
        mock_db.refresh = MagicMock()
        repo.update(obj, {"name": None})
        # name should not be overwritten because value is None
        assert obj.name == "keep"

    def test_delete_existing(self):
        repo, mock_db, FakeModel = self._make_repo()
        obj = FakeModel(id=1)
        mock_db.get.return_value = obj
        result = repo.delete(1)
        mock_db.delete.assert_called_once_with(obj)
        mock_db.commit.assert_called_once()
        assert result == obj

    def test_delete_not_found(self):
        repo, mock_db, FakeModel = self._make_repo()
        mock_db.get.return_value = None
        result = repo.delete(999)
        mock_db.delete.assert_not_called()
        assert result is None


# ===========================================================================
# crud_utils.py
# ===========================================================================

class TestCrudUtils:
    def test_to_update_dict_with_none(self):
        from app.core.crud_utils import _to_update_dict
        result = _to_update_dict(None)
        assert result == {}

    def test_to_update_dict_with_dict(self):
        from app.core.crud_utils import _to_update_dict
        data = {"name": "Alice", "age": 30}
        result = _to_update_dict(data)
        assert result == data

    def test_to_update_dict_with_pydantic(self):
        from app.core.crud_utils import _to_update_dict
        model = MagicMock()
        model.model_dump.return_value = {"field": "value"}
        result = _to_update_dict(model)
        assert result == {"field": "value"}

    def test_utc_now_returns_aware_datetime(self):
        from datetime import timezone
        from app.core.crud_utils import _utc_now
        now = _utc_now()
        assert now.tzinfo == timezone.utc

    def test_apply_updates(self):
        from app.core.crud_utils import _apply_updates

        class Obj:
            name = "old"
            value = 1

        obj = Obj()
        _apply_updates(obj, {"name": "new", "nonexistent": "x"})
        assert obj.name == "new"
        assert obj.value == 1  # unchanged


# ===========================================================================
# core_base.py (SafeBaseModel - list sanitization branch)
# ===========================================================================

class TestSafeBaseModel:
    def test_sanitizes_string(self):
        from app.schemas.core_base import SafeBaseModel
        from pydantic import Field

        class MyModel(SafeBaseModel):
            name: str

        m = MyModel(name="<script>alert(1)</script>")
        assert "<script>" not in m.name
        assert "alert(1)" in m.name  # text is kept, tags stripped

    def test_sanitizes_list_of_strings(self):
        """Covers the list branch (line 20) in recursive_sanitize."""
        from pydantic import Field
        from typing import List
        from app.schemas.core_base import SafeBaseModel

        class ModelWithList(SafeBaseModel):
            tags: List[str]

        m = ModelWithList(tags=["<b>bold</b>", "<script>xss</script>"])
        assert "<b>" not in m.tags[0]
        assert "bold" in m.tags[0]

    def test_sanitizes_dict_values(self):
        """Covers the dict branch in recursive_sanitize."""
        from app.schemas.core_base import SafeBaseModel
        from typing import Optional

        class ModelWithDict(SafeBaseModel):
            meta: Optional[dict] = None

        m = ModelWithDict(meta={"key": "<b>val</b>"})
        assert "<b>" not in m.meta["key"]
        assert "val" in m.meta["key"]

    def test_passthrough_non_string(self):
        """Non-string values should pass through unchanged."""
        from app.schemas.core_base import SafeBaseModel

        class Nums(SafeBaseModel):
            count: int

        m = Nums(count=42)
        assert m.count == 42

