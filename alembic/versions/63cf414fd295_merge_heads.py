"""merge_heads

Revision ID: 63cf414fd295
Revises: c1d2e3f4a5b6, c3d4e5f6a1b2
Create Date: 2026-05-29 23:03:06.678185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63cf414fd295'
down_revision: Union[str, None] = ('c1d2e3f4a5b6', 'c3d4e5f6a1b2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
