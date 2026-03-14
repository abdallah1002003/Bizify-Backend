"""add role to business_invite

Revision ID: 4220423d4437
Revises: 9754ce78cb3b
Create Date: 2026-03-14 01:31:29.917676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4220423d4437'
down_revision: Union[str, None] = '9754ce78cb3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # UC_08: Add role column to business_invite
    with op.batch_alter_table('business_invites', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.Enum('OWNER', 'EDITOR', 'VIEWER', name='collaboratorrole'), nullable=False, server_default='EDITOR'))


def downgrade() -> None:
    with op.batch_alter_table('business_invites', schema=None) as batch_op:
        batch_op.drop_column('role')
