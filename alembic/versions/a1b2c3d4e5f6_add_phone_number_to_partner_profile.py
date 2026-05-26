"""add phone_number to partner_profile

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-05-26 00:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone_number', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.drop_column('phone_number')
