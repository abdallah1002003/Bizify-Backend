"""add guide_status to user_profile

Revision ID: 9754ce78cb3b
Revises: 334d2828d10c
Create Date: 2026-03-14 00:59:00.892751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9754ce78cb3b'
down_revision: Union[str, None] = '334d2828d10c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # UC_07 BF_06: Marks guide as completed, postponed, or skipped
    with op.batch_alter_table('user_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('guide_status', sa.Enum('NOT_STARTED', 'COMPLETED', 'POSTPONED', 'SKIPPED', name='guidestatus'), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('user_profiles', schema=None) as batch_op:
        batch_op.drop_column('guide_status')
