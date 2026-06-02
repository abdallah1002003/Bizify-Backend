"""add budget_detail to ideas

Stores the AI-generated startup-budget breakdown (amount, assumptions, line items,
estimate flag, source) so the idea overview can explain the number and later sync it
to the authoritative Financial-tab (Unit Economics) figure.

Revision ID: a7c1d9e2f3b4
Revises: 326a992b7703
Create Date: 2026-06-02 00:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7c1d9e2f3b4'
down_revision: Union[str, None] = '326a992b7703'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('ideas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('budget_detail', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('ideas', schema=None) as batch_op:
        batch_op.drop_column('budget_detail')
