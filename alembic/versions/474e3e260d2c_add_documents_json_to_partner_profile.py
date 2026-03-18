"""add documents_json to partner_profile

Revision ID: 474e3e260d2c
Revises: 2392777a540f
Create Date: 2026-03-18 15:20:07.451745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '474e3e260d2c'
down_revision: Union[str, None] = '2392777a540f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('documents_json', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.drop_column('documents_json')
