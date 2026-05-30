"""add_mentor_detail_fields_to_partner_profile

Revision ID: d7e8f9a0b1c2
Revises: 23cd9d201be0
Create Date: 2026-05-30 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd7e8f9a0b1c2'
down_revision: Union[str, None] = '23cd9d201be0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('headline', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('about_summary', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('skills_json', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('country', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.drop_column('country')
        batch_op.drop_column('skills_json')
        batch_op.drop_column('about_summary')
        batch_op.drop_column('headline')
