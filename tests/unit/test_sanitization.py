import pytest
from uuid import uuid4
from pydantic import ValidationError
from app.schemas.core_base import SafeBaseModel
from app.schemas.users.user_profile import UserProfileCreate

# 1. Test Raw SafeBaseModel Functionality
class DummyModel(SafeBaseModel):
    name: str
    description: str
    metadata_json: dict

def test_safe_base_model_strips_html():
    malicious_payload = {
        "name": "Hacker <script>alert(1)</script>",
        "description": "<b onmouseover=alert('Wufff!')>click me!</b>",
        "metadata_json": {"nested": "value", "attack": "<iframe src='javascript:alert(1)'>"}
    }
    
    # Instantiate the model with malicious payload
    model = DummyModel(**malicious_payload)
    
    # Assert tags are stripped but content remains
    assert model.name == "Hacker alert(1)" # Extracted text only
    assert model.description == "click me!" # Stripped tags and dangerous attributes
    
    # Test JSON recursively behaves properly
    assert model.metadata_json["nested"] == "value"
    # The JSON string field should also be sanitized
    assert model.metadata_json["attack"] == ""


# 2. Test Integration with Real Schema (UserProfile)
def test_user_profile_bio_sanitization():
    xss_bio = "<img src='x' onerror='alert(document.cookie)'> malicious bio <a href='javascript:alert(1)'>link</a>"
    
    profile_data = {
        "user_id": uuid4(),
        "bio": xss_bio,
    }
    
    profile = UserProfileCreate(**profile_data)
    
    # The image and link tags should be gone
    assert profile.bio == "malicious bio link"

def test_business_context_json_sanitization():
    from app.schemas.business.business import BusinessCreate
    from app.models.enums import BusinessStage
    
    malicious_json = {
        "name": "<script>console.log('pwned')</script>Evil Corp",
        "description": "<div style='background: url(javascript:alert(1))'>Test</div>"
    }
    
    bus = BusinessCreate(
        owner_id=uuid4(),
        stage=BusinessStage.EARLY,
        context_json=malicious_json,
    )
    
    assert bus.context_json["name"] == "console.log('pwned')Evil Corp"
    assert bus.context_json["description"] == "Test"
