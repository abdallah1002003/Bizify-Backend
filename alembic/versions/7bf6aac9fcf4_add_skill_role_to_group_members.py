"""add_skill_role_to_group_members

Revision ID: 7bf6aac9fcf4
Revises: b3c4d5e6f7a8
Create Date: 2026-06-03 11:04:31.386368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '7bf6aac9fcf4'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('group_members', schema=None) as batch_op:
        batch_op.add_column(sa.Column('skill_role', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('group_members', schema=None) as batch_op:
        batch_op.drop_column('skill_role')
