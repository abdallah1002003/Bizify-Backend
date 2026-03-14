"""add_last_activity_to_user

Revision ID: 750d4702483c
Revises: 799587d8e05a
Create Date: 2026-03-14 02:14:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '750d4702483c'
down_revision: Union[str, None] = '799587d8e05a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # UC_09: Add last_activity to users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_activity', sa.DateTime(), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_activity')
