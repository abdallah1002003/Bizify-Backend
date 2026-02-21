"""Backward-compatible config facade.

Use `config.settings.settings` as the single source of truth.
"""

from config.settings import settings  # re-export for legacy imports


def get_settings():
    return settings
