from app.core.config import get_settings
from config.settings import settings

def test_get_settings():
    assert get_settings() == settings
