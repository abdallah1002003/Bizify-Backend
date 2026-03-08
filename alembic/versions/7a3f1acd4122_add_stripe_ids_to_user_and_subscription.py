"""add_stripe_ids_to_user_and_subscription

Revision ID: 7a3f1acd4122
Revises: 2cce88cc35c7
Create Date: 2026-02-24 12:08:34.345821

Adds:
- subscriptions.stripe_subscription_id  (e.g. sub_Xyz...)
- users.stripe_customer_id              (e.g. cus_Xyz...)

Both columns are nullable and unique-indexed so Stripe webhook handlers can
map incoming Stripe IDs to local DB rows efficiently.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a3f1acd4122'
down_revision: Union[str, None] = '2cce88cc35c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('subscriptions', sa.Column('stripe_subscription_id', sa.String(), nullable=True))
    op.create_index(
        op.f('ix_subscriptions_stripe_subscription_id'),
        'subscriptions',
        ['stripe_subscription_id'],
        unique=True,
    )

    op.add_column('users', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    op.create_index(
        op.f('ix_users_stripe_customer_id'),
        'users',
        ['stripe_customer_id'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_column('users', 'stripe_customer_id')

    op.drop_index(op.f('ix_subscriptions_stripe_subscription_id'), table_name='subscriptions')
    op.drop_column('subscriptions', 'stripe_subscription_id')
