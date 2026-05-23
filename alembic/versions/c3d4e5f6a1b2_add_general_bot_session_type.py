"""add_general_bot_session_type

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-05-23 00:00:00.000000

Adds GENERAL_BOT to the sessiontype enum so the AI general-chat bot
can persist conversation history in chat_sessions.
Without this, the AI service raises:
  invalid input value for enum sessiontype: "GENERAL_BOT"
"""
from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = 'c3d4e5f6a1b2'
down_revision: Union[str, None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE … ADD VALUE for existing enum types.
    # IF NOT EXISTS avoids errors on re-runs (idempotent).
    op.execute("ALTER TYPE sessiontype ADD VALUE IF NOT EXISTS 'GENERAL_BOT'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type.
    # Leave the value in place — it simply won't be used.
    pass
