"""add_partner_categories_table

Revision ID: 5e9a39ce4e13
Revises: 23cd9d201be0
Create Date: 2026-05-30 00:03:18.624955

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

revision: str = '5e9a39ce4e13'
down_revision: Union[str, None] = '23cd9d201be0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'partner_categories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column(
            'partner_type',
            PgEnum('MENTOR', 'SUPPLIER', 'MANUFACTURER', name='partnertype', create_type=False),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.UUID(), nullable=True))
        batch_op.create_foreign_key(
            'fk_partner_profiles_category_id',
            'partner_categories',
            ['category_id'],
            ['id'],
        )
        batch_op.drop_column('category')


def downgrade() -> None:
    with op.batch_alter_table('partner_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(), nullable=True))
        batch_op.drop_constraint('fk_partner_profiles_category_id', type_='foreignkey')
        batch_op.drop_column('category_id')

    op.drop_table('partner_categories')
