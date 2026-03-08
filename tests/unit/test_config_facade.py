from app.core.config import get_settings, settings


def test_config_facade_returns_singleton_settings():
    assert get_settings() is settings
