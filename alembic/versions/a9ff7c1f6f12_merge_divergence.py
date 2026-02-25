"""merge divergence

Revision ID: a9ff7c1f6f12
Revises: 64bda0428c70, add_foreign_key_indexes
Create Date: 2026-02-24 17:37:36.834025

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = 'a9ff7c1f6f12'
down_revision: Union[str, None] = ('64bda0428c70', 'add_foreign_key_indexes')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
