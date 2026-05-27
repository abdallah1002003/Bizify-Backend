"""add idea seed fields to ideas table

Revision ID: c1d2e3f4a5b6
Revises: f6a7b8c9d0e1
Create Date: 2026-05-28 00:00:00.000000

Adds the five AI-generated seed columns to the ideas table:
  domain, problem_evidence, core_insight, target_segment, founding_hypothesis

These replace the old markdown-blob approach where the AI service
parsed text with regex to extract idea metadata. Now the LLM outputs
structured JSON and writes directly to these columns.
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_COLUMNS: list[tuple[str, sa.Column]] = [
    ('domain',              sa.Column('domain',              sa.String(),  nullable=True)),
    ('problem_evidence',    sa.Column('problem_evidence',    sa.JSON(),    nullable=True)),
    ('core_insight',        sa.Column('core_insight',        sa.Text(),    nullable=True)),
    ('target_segment',      sa.Column('target_segment',      sa.Text(),    nullable=True)),
    ('founding_hypothesis', sa.Column('founding_hypothesis', sa.Text(),    nullable=True)),
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'ideas' not in set(inspector.get_table_names()):
        return

    existing_columns = {col['name'] for col in inspector.get_columns('ideas')}

    with op.batch_alter_table('ideas', schema=None) as batch_op:
        for column_name, column in _NEW_COLUMNS:
            if column_name not in existing_columns:
                batch_op.add_column(column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'ideas' not in set(inspector.get_table_names()):
        return

    existing_columns = {col['name'] for col in inspector.get_columns('ideas')}

    with op.batch_alter_table('ideas', schema=None) as batch_op:
        for column_name, _ in reversed(_NEW_COLUMNS):
            if column_name in existing_columns:
                batch_op.drop_column(column_name)
