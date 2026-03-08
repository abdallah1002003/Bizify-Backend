"""add_email_verification_tokens

Revision ID: 2cce88cc35c7
Revises: 2f0cced2ae5d
Create Date: 2026-02-24 11:30:09.612135

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.guid import GUID


# revision identifiers, used by Alembic.
revision: str = '2cce88cc35c7'
down_revision: Union[str, None] = '2f0cced2ae5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('jti', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_email_verification_tokens_jti'),
        'email_verification_tokens', ['jti'], unique=True,
    )
    op.create_index(
        op.f('ix_email_verification_tokens_used'),
        'email_verification_tokens', ['used'], unique=False,
    )
    op.create_index(
        op.f('ix_email_verification_tokens_user_id'),
        'email_verification_tokens', ['user_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_email_verification_tokens_user_id'), table_name='email_verification_tokens')
    op.drop_index(op.f('ix_email_verification_tokens_used'), table_name='email_verification_tokens')
    op.drop_index(op.f('ix_email_verification_tokens_jti'), table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
