"""
Pydantic schema validator tests for:
  - app/schemas/billing/plan.py     (PlanCreate / PlanUpdate validators)
  - app/schemas/users/user_profile.py (UserProfile validators)
  - app/schemas/partners/partner_profile.py (PartnerProfile validators)
"""
import uuid
import pytest
from pydantic import ValidationError


# ===========================================================================
# plan.py — PlanCreate.validate_features_json
# ===========================================================================

class TestPlanCreateValidator:
    def test_none_returns_empty_dict(self):
        from app.schemas.billing.plan import PlanCreate
        p = PlanCreate(name="Basic", price=9.99, features_json=None)
        assert p.features_json == {}

    def test_valid_dict_passes(self):
        from app.schemas.billing.plan import PlanCreate
        p = PlanCreate(name="Pro", price=29.99, features_json={"max_users": 10})
        assert p.features_json == {"max_users": 10}

    def test_invalid_type_raises(self):
        from app.schemas.billing.plan import PlanCreate
        with pytest.raises(ValidationError):
            PlanCreate(name="X", price=1.0, features_json="not a dict")

    def test_non_serializable_value_raises(self):
        from app.schemas.billing.plan import PlanCreate
        with pytest.raises(ValidationError):
            PlanCreate(name="X", price=1.0, features_json={"bad": object()})


class TestPlanUpdateValidator:
    def test_none_returns_none(self):
        from app.schemas.billing.plan import PlanUpdate
        p = PlanUpdate(features_json=None)
        assert p.features_json is None

    def test_valid_dict_passes(self):
        from app.schemas.billing.plan import PlanUpdate
        p = PlanUpdate(features_json={"feature": "on"})
        assert p.features_json == {"feature": "on"}

    def test_invalid_type_raises(self):
        from app.schemas.billing.plan import PlanUpdate
        with pytest.raises(ValidationError):
            PlanUpdate(features_json=["list", "not", "dict"])

    def test_non_serializable_raises(self):
        from app.schemas.billing.plan import PlanUpdate
        with pytest.raises(ValidationError):
            PlanUpdate(features_json={"bad": set([1, 2, 3])})


# ===========================================================================
# user_profile.py — validators in Base, Create, Update
# ===========================================================================

class TestUserProfileBaseValidator:
    def _uid(self):
        return uuid.uuid4()

    def test_none_json_returns_empty_dict(self):
        from app.schemas.users.user_profile import UserProfileBase
        p = UserProfileBase(user_id=self._uid(), bio="Hello", skills_json=None)
        assert p.skills_json == {}

    def test_valid_dict_passes(self):
        from app.schemas.users.user_profile import UserProfileBase
        p = UserProfileBase(user_id=self._uid(), bio="Bio", skills_json={"python": True})
        assert p.skills_json == {"python": True}

    def test_invalid_type_raises(self):
        from app.schemas.users.user_profile import UserProfileBase
        with pytest.raises(ValidationError):
            UserProfileBase(user_id=self._uid(), bio="Bio", skills_json="bad")

    def test_non_serializable_raises(self):
        from app.schemas.users.user_profile import UserProfileBase
        with pytest.raises(ValidationError):
            UserProfileBase(user_id=self._uid(), bio="Bio", skills_json={"x": object()})


class TestUserProfileCreateValidator:
    def _uid(self):
        return uuid.uuid4()

    def test_none_json_returns_empty_dict(self):
        from app.schemas.users.user_profile import UserProfileCreate
        p = UserProfileCreate(user_id=self._uid(), bio="Hi", interests_json=None)
        assert p.interests_json == {}

    def test_invalid_type_raises(self):
        from app.schemas.users.user_profile import UserProfileCreate
        with pytest.raises(ValidationError):
            UserProfileCreate(user_id=self._uid(), bio="Hi", interests_json=123)


class TestUserProfileUpdateValidator:
    def test_none_json_returns_none(self):
        from app.schemas.users.user_profile import UserProfileUpdate
        p = UserProfileUpdate(skills_json=None)
        assert p.skills_json is None

    def test_valid_dict_passes(self):
        from app.schemas.users.user_profile import UserProfileUpdate
        p = UserProfileUpdate(preferences_json={"theme": "dark"})
        assert p.preferences_json == {"theme": "dark"}

    def test_invalid_type_raises(self):
        from app.schemas.users.user_profile import UserProfileUpdate
        with pytest.raises(ValidationError):
            UserProfileUpdate(skills_json="string")

    def test_non_serializable_raises(self):
        from app.schemas.users.user_profile import UserProfileUpdate
        with pytest.raises(ValidationError):
            UserProfileUpdate(risk_profile_json={"bad": lambda x: x})


# ===========================================================================
# partner_profile.py schema validator tests
# ===========================================================================

class TestPartnerProfileSchemaValidator:
    def test_create_valid(self):
        from app.schemas.partners.partner_profile import PartnerProfileCreate
        from app.models.enums import PartnerType
        p = PartnerProfileCreate(
            user_id=uuid.uuid4(),
            partner_type=PartnerType.MENTOR,
            company_name="Acme",
        )
        assert p.company_name == "Acme"

    def test_create_none_json_returns_empty_dict(self):
        from app.schemas.partners.partner_profile import PartnerProfileCreate
        from app.models.enums import PartnerType
        p = PartnerProfileCreate(
            user_id=uuid.uuid4(),
            partner_type=PartnerType.MENTOR,
            services_json=None,
        )
        assert p.services_json == {}

    def test_create_invalid_json_type_raises(self):
        from app.schemas.partners.partner_profile import PartnerProfileCreate
        from app.models.enums import PartnerType
        with pytest.raises(ValidationError):
            PartnerProfileCreate(
                user_id=uuid.uuid4(),
                partner_type=PartnerType.MENTOR,
                services_json="not a dict",
            )

    def test_create_non_serializable_raises(self):
        from app.schemas.partners.partner_profile import PartnerProfileCreate
        from app.models.enums import PartnerType
        with pytest.raises(ValidationError):
            PartnerProfileCreate(
                user_id=uuid.uuid4(),
                partner_type=PartnerType.MENTOR,
                experience_json={"bad": object()},
            )

    def test_update_none_returns_none(self):
        from app.schemas.partners.partner_profile import PartnerProfileUpdate
        p = PartnerProfileUpdate(services_json=None)
        assert p.services_json is None

    def test_update_valid_dict(self):
        from app.schemas.partners.partner_profile import PartnerProfileUpdate
        p = PartnerProfileUpdate(experience_json={"years": 5})
        assert p.experience_json == {"years": 5}

    def test_update_invalid_type_raises(self):
        from app.schemas.partners.partner_profile import PartnerProfileUpdate
        with pytest.raises(ValidationError):
            PartnerProfileUpdate(services_json=[1, 2, 3])

