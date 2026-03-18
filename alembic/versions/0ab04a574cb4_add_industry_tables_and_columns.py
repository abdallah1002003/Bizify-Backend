"""Add industry tables and columns

Revision ID: 0ab04a574cb4
Revises: 81a77318d854
Create Date: 2026-03-16 23:23:24.198329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ab04a574cb4'
down_revision: Union[str, None] = '81a77318d854'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create industries table
    op.create_table('industries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['industries.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 2. Add industry_id to businesses
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('industry_id', sa.UUID(), nullable=True))
        batch_op.create_foreign_key('fk_business_industry', 'industries', ['industry_id'], ['id'])

    # 3. Add industry_id to skill_benchmarks
    with op.batch_alter_table('skill_benchmarks', schema=None) as batch_op:
        # Note: Making it nullable=True first to avoid issues with existing data
        batch_op.add_column(sa.Column('industry_id', sa.UUID(), nullable=True))
        batch_op.create_foreign_key('fk_skill_benchmark_industry', 'industries', ['industry_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('skill_benchmarks', schema=None) as batch_op:
        batch_op.drop_constraint('fk_skill_benchmark_industry', type_='foreignkey')
        batch_op.drop_column('industry_id')

    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_business_industry', type_='foreignkey')
        batch_op.drop_column('industry_id')

    op.drop_table('industries')
