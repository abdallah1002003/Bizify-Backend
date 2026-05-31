"""convert_idea_budget_to_egp

One-time data migration: existing idea budgets were generated/stored in USD.
The product now uses EGP natively, so multiply every existing idea.budget by the
fixed conversion rate (50 EGP per 1 USD) so historical ideas match the new
EGP-native budgets and the EGP budget filter bands.

Revision ID: f2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-05-31 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f2b3c4d5e6f7'
down_revision: Union[str, None] = 'e1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EGP_PER_USD = 50


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE ideas SET budget = budget * :rate WHERE budget IS NOT NULL"),
        {"rate": EGP_PER_USD},
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("UPDATE ideas SET budget = budget / :rate WHERE budget IS NOT NULL"),
        {"rate": EGP_PER_USD},
    )
