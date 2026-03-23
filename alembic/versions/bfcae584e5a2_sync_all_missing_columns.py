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
    collaborator_status_enum = sa.Enum('active', 'removal_pending', name='collaboratorstatus')
    collaborator_status_enum.create(op.get_bind(), checkfirst=True)
    collaborator_role_enum = sa.Enum('OWNER', 'EDITOR', 'VIEWER', name='collaboratorrole')
    collaborator_role_enum.create(op.get_bind(), checkfirst=True)
    notification_status_enum = sa.Enum('unread', 'read', 'dismissed', 'archived', name='notificationstatus')
    notification_status_enum.create(op.get_bind(), checkfirst=True)
    delivery_status_enum = sa.Enum('pending', 'sent', 'failed', name='deliverystatus')
    delivery_status_enum.create(op.get_bind(), checkfirst=True)

    # Table: ideas
    with op.batch_alter_table('ideas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_score_outdated', sa.Boolean(), nullable=True, server_default=sa.text('false')))

    # Table: business_collaborators
    with op.batch_alter_table('business_collaborators', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', collaborator_status_enum, nullable=False, server_default='active'))

    # Table: business_join_requests
    with op.batch_alter_table('business_join_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', collaborator_role_enum, nullable=False, server_default='VIEWER'))

    # Table: notifications
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', notification_status_enum, nullable=False, server_default='unread'))
        batch_op.add_column(sa.Column('delivery_status', delivery_status_enum, nullable=False, server_default='pending'))
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

    # Drop Enums
    sa.Enum('active', 'removal_pending', name='collaboratorstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum('OWNER', 'EDITOR', 'VIEWER', name='collaboratorrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum('unread', 'read', 'dismissed', 'archived', name='notificationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum('pending', 'sent', 'failed', name='deliverystatus').drop(op.get_bind(), checkfirst=True)
