"""add_token_blacklist_index

Revision ID: a1b2c3d4e5f6
Revises: d1f3a5c9b802
Create Date: 2026-05-18 00:00:00.000000

Adds an index on token_blacklist.blacklisted_at so that the TTL-based
is_token_blacklisted() query (which filters by blacklisted_at >= cutoff)
does not do a sequential scan of the entire table.

Also adds an index on token_blacklist.token to speed up the primary
exact-match lookup if the primary-key index is not already being used.
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd1f3a5c9b802'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_token_blacklist_blacklisted_at',
        'token_blacklist',
        ['blacklisted_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_token_blacklist_blacklisted_at', table_name='token_blacklist')
