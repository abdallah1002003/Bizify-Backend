"""add overview_detail to ideas table

Revision ID: d2e3f4a5b6c7
Revises: 7bf6aac9fcf4
Create Date: 2026-06-03 00:00:00.000000

Adds the decision-grade Overview block written by the AI service:
  overview_detail = {value_proposition, founder_market_fit, strategic_advantage,
                     execution_advantage, why_now, why_this_should_exist}

Nullable + additive. Mirrors the column added on the AI service side
(bizifyAI migration_overview_detail.sql / db/models.py Idea.overview_detail).
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = '7bf6aac9fcf4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'ideas' not in set(inspector.get_table_names()):
        return

    existing_columns = {col['name'] for col in inspector.get_columns('ideas')}

    if 'overview_detail' not in existing_columns:
        with op.batch_alter_table('ideas', schema=None) as batch_op:
            batch_op.add_column(sa.Column('overview_detail', sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'ideas' not in set(inspector.get_table_names()):
        return

    existing_columns = {col['name'] for col in inspector.get_columns('ideas')}

    if 'overview_detail' in existing_columns:
        with op.batch_alter_table('ideas', schema=None) as batch_op:
            batch_op.drop_column('overview_detail')
