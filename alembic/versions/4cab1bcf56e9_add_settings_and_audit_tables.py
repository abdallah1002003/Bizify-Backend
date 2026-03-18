"""add_settings_and_audit_tables

Revision ID: 4cab1bcf56e9
Revises: f5d57f71ac20
Create Date: 2026-03-17 13:08:10.985209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cab1bcf56e9'
down_revision: Union[str, None] = 'f5d57f71ac20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('privacy_settings',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('visibility', sa.String(), nullable=True),
        sa.Column('show_contact_info', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )

    op.create_table('audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_password_change', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_password_change')
    op.drop_table('audit_logs')
    op.drop_table('privacy_settings')
def downgrade() -> None:
    pass