"""sync all missing columns

Revision ID: bfcae584e5a2
Revises: 474e3e260d2c
Create Date: 2026-03-18 15:24:00.365970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfcae584e5a2'
down_revision: Union[str, None] = '474e3e260d2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Table: ideas
    with op.batch_alter_table('ideas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_score_outdated', sa.Boolean(), nullable=True, server_default=sa.text('0')))

    # Table: business_collaborators
    with op.batch_alter_table('business_collaborators', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Enum('active', 'removal_pending', name='collaboratorstatus'), nullable=False, server_default='active'))

    # Table: business_join_requests
    with op.batch_alter_table('business_join_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.Enum('owner', 'editor', 'viewer', name='collaboratorrole'), nullable=False, server_default='viewer'))

    # Table: notifications
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.Enum('unread', 'read', 'dismissed', 'archived', name='notificationstatus'), nullable=False, server_default='unread'))
        batch_op.add_column(sa.Column('delivery_status', sa.Enum('pending', 'sent', 'failed', name='deliverystatus'), nullable=False, server_default='pending'))
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), nullable=True, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Table: notifications
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_column('expires_at')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('delivery_status')
        batch_op.drop_column('status')

    # Table: business_join_requests
    with op.batch_alter_table('business_join_requests', schema=None) as batch_op:
        batch_op.drop_column('role')

    # Table: business_collaborators
    with op.batch_alter_table('business_collaborators', schema=None) as batch_op:
        batch_op.drop_column('status')

    # Table: ideas
    with op.batch_alter_table('ideas', schema=None) as batch_op:
        batch_op.drop_column('is_score_outdated')
