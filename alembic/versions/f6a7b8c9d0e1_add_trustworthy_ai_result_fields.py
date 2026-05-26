"""add trustworthy ai result fields

Revision ID: f6a7b8c9d0e1
Revises: f2c8a91d3e01
Create Date: 2026-05-26 00:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'f2c8a91d3e01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COLUMNS: dict[str, list[tuple[str, sa.Column]]] = {
    'customers_results': [
        ('customer_journey_map', sa.Column('customer_journey_map', sa.JSON(), nullable=True)),
    ],
    'competition_results': [
        ('your_opening', sa.Column('your_opening', sa.Text(), nullable=True)),
    ],
    'mvp_planning_results': [
        ('milestones', sa.Column('milestones', sa.JSON(), nullable=True)),
    ],
    'unit_economics_results': [
        ('scenarios', sa.Column('scenarios', sa.JSON(), nullable=True)),
    ],
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name, columns in _COLUMNS.items():
        if table_name not in existing_tables:
            continue
        existing_columns = {column['name'] for column in inspector.get_columns(table_name)}
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            for column_name, column in columns:
                if column_name not in existing_columns:
                    batch_op.add_column(column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name, columns in reversed(_COLUMNS.items()):
        if table_name not in existing_tables:
            continue
        existing_columns = {column['name'] for column in inspector.get_columns(table_name)}
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            for column_name, _column in reversed(columns):
                if column_name in existing_columns:
                    batch_op.drop_column(column_name)
