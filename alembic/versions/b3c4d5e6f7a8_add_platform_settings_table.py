"""add_platform_settings_table

Revision ID: b3c4d5e6f7a8
Revises: a1bfef8c7250
Create Date: 2026-06-03 12:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a1bfef8c7250"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_platform_settings_key", "platform_settings", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_platform_settings_key", table_name="platform_settings")
    op.drop_table("platform_settings")
