"""add phone_number to partner_profile

Revision ID: a1b2c3d4e5f7
Revises: f6a7b8c9d0e1
Create Date: 2026-05-26 00:00:00.000000

Note: this migration originally shared the revision id 'a1b2c3d4e5f6' with
add_otp_attempts (a copy-paste collision that broke the Alembic graph). It has
been given the unique id 'a1b2c3d4e5f7'; its parent (f6a7b8c9d0e1) is unchanged.
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    # Idempotent: under the old duplicate revision id 'a1b2c3d4e5f6' this column
    # may already have been applied on some databases. Skip if it already exists.
    if not _has_column('partner_profiles', 'phone_number'):
        with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
            batch_op.add_column(sa.Column('phone_number', sa.String(), nullable=True))


def downgrade() -> None:
    if _has_column('partner_profiles', 'phone_number'):
        with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
            batch_op.drop_column('phone_number')
