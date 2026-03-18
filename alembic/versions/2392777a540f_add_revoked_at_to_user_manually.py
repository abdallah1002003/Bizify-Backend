"""add revoked_at to user manually

Revision ID: 2392777a540f
Revises: 4040ed93e9fb
Create Date: 2026-03-18 15:08:15.250515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2392777a540f'
down_revision: Union[str, None] = '4040ed93e9fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add revoked_at to users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('revoked_at', sa.DateTime(), nullable=True))

    # 2. Add missing columns to notifications (as seen in the models)
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        # Check if they exist before adding to avoid errors if partially migrated
        batch_op.add_column(sa.Column('content', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('type', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_column('type')
        batch_op.drop_column('content')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('revoked_at')
