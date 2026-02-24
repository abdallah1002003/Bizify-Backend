"""Backward-compatible config facade.

Use `config.settings.settings` as the single source of truth.
"""

from config.settings import settings, Settings


def get_settings() -> Settings:
    return settings
