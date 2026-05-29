"""add_category_and_linkedin_to_partner_profile

Revision ID: 23cd9d201be0
Revises: 63cf414fd295
Create Date: 2026-05-29 23:03:16.438605

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '23cd9d201be0'
down_revision: Union[str, None] = '63cf414fd295'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('linkedin_url', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.drop_column('linkedin_url')
        batch_op.drop_column('category')
