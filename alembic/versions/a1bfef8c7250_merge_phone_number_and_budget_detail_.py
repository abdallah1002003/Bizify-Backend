"""merge phone_number and budget_detail heads

Revision ID: a1bfef8c7250
Revises: a1b2c3d4e5f7, a7c1d9e2f3b4
Create Date: 2026-06-02 21:18:26.255016

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1bfef8c7250'
down_revision: Union[str, None] = ('a1b2c3d4e5f7', 'a7c1d9e2f3b4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
