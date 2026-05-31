"""add profile_views table

Revision ID: 326a992b7703
Revises: f2b3c4d5e6f7
Create Date: 2026-05-31 17:22:07.014998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '326a992b7703'
down_revision: Union[str, None] = 'f2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'profile_views',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('partner_id', sa.UUID(as_uuid=True), sa.ForeignKey('partner_profiles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('viewer_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('viewer_name', sa.String(), nullable=True),
        sa.Column('viewer_email', sa.String(), nullable=True),
        sa.Column('viewer_role', sa.String(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('profile_views')
