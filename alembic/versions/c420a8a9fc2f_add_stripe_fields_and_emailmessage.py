"""Add Stripe fields and EmailMessage

Revision ID: c420a8a9fc2f
Revises: 77f57981c630
Create Date: 2026-02-25 05:29:04.110596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.db.guid

# revision identifiers, used by Alembic.
revision: str = 'c420a8a9fc2f'
down_revision: Union[str, None] = '77f57981c630'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # email_messages table
    op.create_table('email_messages',
    sa.Column('id', app.db.guid.GUID(), nullable=False),
    sa.Column('to_email', sa.String(), nullable=False),
    sa.Column('subject', sa.String(), nullable=False),
    sa.Column('html_body', sa.Text(), nullable=False),
    sa.Column('status', sa.String(), server_default='PENDING', nullable=False),
    sa.Column('retries', sa.Integer(), server_default='0', nullable=False),
    sa.Column('max_retries', sa.Integer(), server_default='3', nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_messages_status'), 'email_messages', ['status'], unique=False)
    op.create_index(op.f('ix_email_messages_to_email'), 'email_messages', ['to_email'], unique=False)

    # plans table changes
    op.add_column('plans', sa.Column('stripe_price_id', sa.String(), nullable=True))
    op.add_column('plans', sa.Column('billing_cycle', sa.String(), server_default='month', nullable=False))
    op.create_index(op.f('ix_plans_stripe_price_id'), 'plans', ['stripe_price_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_plans_stripe_price_id'), table_name='plans')
    op.drop_column('plans', 'billing_cycle')
    op.drop_column('plans', 'stripe_price_id')

    op.drop_index(op.f('ix_email_messages_to_email'), table_name='email_messages')
    op.drop_index(op.f('ix_email_messages_status'), table_name='email_messages')
    op.drop_table('email_messages')
