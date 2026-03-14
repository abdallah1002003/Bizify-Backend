"""Add token blacklist table

Revision ID: 3c6920e45405
Revises: ac74ce78f81a
Create Date: 2026-03-13 15:44:36.457469

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3c6920e45405'
down_revision: Union[str, None] = 'ac74ce78f81a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('token_blacklist',
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('blacklisted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('token')
    )
    with op.batch_alter_table('token_blacklist', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_token_blacklist_token'), ['token'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('token_blacklist', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_token_blacklist_token'))
    op.drop_table('token_blacklist')
