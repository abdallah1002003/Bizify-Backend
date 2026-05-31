"""add_partner_rich_fields

Adds a single details_json column to partner_profiles to store rich
supplier/manufacturer data (contacts, location, products, capabilities, etc.)
without requiring dozens of individual schema columns.

Revision ID: e1a2b3c4d5e6
Revises: 3cd21a1f0fdf
Create Date: 2026-05-31 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, None] = '3cd21a1f0fdf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('details_json', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.drop_column('details_json')
