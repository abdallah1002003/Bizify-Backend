"""rename_skill_fields_uc11

Revision ID: 81a77318d854
Revises: ae2e68818ccc
Create Date: 2026-03-16 19:27:19.046897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81a77318d854'
down_revision: Union[str, None] = 'ae2e68818ccc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename user_skills.rating to declared_level
    with op.batch_alter_table('user_skills', schema=None) as batch_op:
        batch_op.alter_column('rating', new_column_name='declared_level')

    # Rename skill_benchmarks.min_required_level to minimum_required_level
    with op.batch_alter_table('skill_benchmarks', schema=None) as batch_op:
        batch_op.alter_column('min_required_level', new_column_name='minimum_required_level')


def downgrade() -> None:
    # Revert skill_benchmarks.minimum_required_level to min_required_level
    with op.batch_alter_table('skill_benchmarks', schema=None) as batch_op:
        batch_op.alter_column('minimum_required_level', new_column_name='min_required_level')

    # Revert user_skills.declared_level to rating
    with op.batch_alter_table('user_skills', schema=None) as batch_op:
        batch_op.alter_column('declared_level', new_column_name='rating')
