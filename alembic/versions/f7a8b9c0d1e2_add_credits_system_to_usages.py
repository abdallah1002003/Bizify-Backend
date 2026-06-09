"""Add credit system columns to usages table

Revision ID: f7a8b9c0d1e2
Revises: e33f0f822d3b
Create Date: 2026-06-08 00:00:00.000000

Adds:
  - credits_used       INTEGER DEFAULT 0   -- credits spent this billing period
  - credits_limit      INTEGER DEFAULT 15  -- allowance (15 Free, 90 Pro, 150 Premium)
  - period_start       DATE                -- billing period start date
  - chat_turns_today   INTEGER DEFAULT 0   -- daily general-chat turn counter
  - chat_turns_date    DATE                -- date the turn counter was last reset
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, None] = "e33f0f822d3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usages", sa.Column("credits_used",      sa.Integer(), nullable=True, server_default="0"))
    op.add_column("usages", sa.Column("credits_limit",     sa.Integer(), nullable=True, server_default="15"))
    op.add_column("usages", sa.Column("period_start",      sa.Date(),    nullable=True))
    op.add_column("usages", sa.Column("chat_turns_today",  sa.Integer(), nullable=True, server_default="0"))
    op.add_column("usages", sa.Column("chat_turns_date",   sa.Date(),    nullable=True))

    # Ensure ppf columns exist (they were added to the model but may be missing in older DBs)
    with op.get_context().autocommit_block():
        pass
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing = {c["name"] for c in insp.get_columns("usages")}
    if "ppf_purchased" not in existing:
        op.add_column("usages", sa.Column("ppf_purchased", sa.Integer(), nullable=True, server_default="0"))
    if "ppf_used" not in existing:
        op.add_column("usages", sa.Column("ppf_used",      sa.Integer(), nullable=True, server_default="0"))


def downgrade() -> None:
    for col in ("credits_used", "credits_limit", "period_start", "chat_turns_today", "chat_turns_date"):
        op.drop_column("usages", col)
