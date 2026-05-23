"""add_pending_subscription_status

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-05-19 00:00:00.000000

Adds PENDING to the subscriptionstatus enum so Paymob card payments
can create a subscription before the webhook confirms the payment.
"""
from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE … ADD VALUE for existing enum types.
    # IF NOT EXISTS avoids errors on re-runs.
    op.execute("ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'PENDING'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type.
    # The safest downgrade is to leave the value in place (it just won't be used).
    pass
