"""manual_add_last_activity

Revision ID: 1cba93387549
Revises: 750d4702483c
Create Date: 2026-03-14 02:18:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cba93387549'
down_revision: Union[str, None] = '750d4702483c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adding last_activity column to users table safely for SQLite
    # Turned into a no-op because 750d4702483c already adds this column
    pass


def downgrade() -> None:
    pass
