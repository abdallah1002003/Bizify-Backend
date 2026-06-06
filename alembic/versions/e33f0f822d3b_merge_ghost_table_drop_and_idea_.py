"""merge ghost-table drop and idea_favorites heads

Revision ID: e33f0f822d3b
Revises: e3f4a5b6c7d8, a2b3c4d5e6f7
Create Date: 2026-06-06 20:03:42.550357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e33f0f822d3b'
down_revision: Union[str, None] = ('e3f4a5b6c7d8', 'a2b3c4d5e6f7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
