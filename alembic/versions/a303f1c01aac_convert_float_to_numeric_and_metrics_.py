"""convert_float_to_numeric_and_metrics_cleanup

Revision ID: a303f1c01aac
Revises: 5cc0f303f64a
Create Date: 2026-02-26 12:19:31.894703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a303f1c01aac'
down_revision: Union[str, None] = '5cc0f303f64a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert plans.price from Float to Numeric(10, 2)
    op.alter_column('plans', 'price',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)
    
    # Convert payments.amount from Float to Numeric(10, 2)
    op.alter_column('payments', 'amount',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)


def downgrade() -> None:
    # Convert payments.amount back to Float
    op.alter_column('payments', 'amount',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)

    # Convert plans.price back to Float
    op.alter_column('plans', 'price',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)
