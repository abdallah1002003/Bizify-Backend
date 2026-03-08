"""merge heads fix

Revision ID: merge_heads_fix
Revises: a303f1c01aac, b1e2f3a4d5c6
Create Date: 2026-03-07 21:26:00.000000

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'merge_heads_fix'
down_revision: Union[str, None] = ('a303f1c01aac', 'b1e2f3a4d5c6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
