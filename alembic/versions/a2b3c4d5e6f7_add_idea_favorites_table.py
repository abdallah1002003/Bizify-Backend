"""add idea_favorites table

Revision ID: a2b3c4d5e6f7
Revises: d2e3f4a5b6c7
Create Date: 2026-06-05 00:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idea_favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "idea_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ideas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "idea_id", name="uq_idea_favorite"),
    )
    op.create_index("ix_idea_favorites_user_id", "idea_favorites", ["user_id"])
    op.create_index("ix_idea_favorites_idea_id", "idea_favorites", ["idea_id"])


def downgrade() -> None:
    op.drop_index("ix_idea_favorites_idea_id", table_name="idea_favorites")
    op.drop_index("ix_idea_favorites_user_id", table_name="idea_favorites")
    op.drop_table("idea_favorites")
