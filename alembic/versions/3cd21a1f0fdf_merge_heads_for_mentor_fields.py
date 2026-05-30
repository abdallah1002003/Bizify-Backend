"""merge_heads_for_mentor_fields

Revision ID: 3cd21a1f0fdf
Revises: 5e9a39ce4e13, d7e8f9a0b1c2
Create Date: 2026-05-30 12:57:56.771761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cd21a1f0fdf'
down_revision: Union[str, None] = ('5e9a39ce4e13', 'd7e8f9a0b1c2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
