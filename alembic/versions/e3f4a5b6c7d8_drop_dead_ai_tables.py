"""drop dead AI ghost tables

Removes 11 tables that were defined as ORM models but never wired to any
API route, service, or repository (the original ``app/models/ai`` schema that
the standalone bizifyAI service replaced, plus the first-gen roadmap tables
superseded by ``execution_*``).

Verified against the live DB on 2026-06-06: all empty except ``agents`` (13
rows of static seed data that nothing reads at runtime).

Dropped with CASCADE + IF EXISTS so inter-table foreign keys are removed in
any order. This is a one-way cleanup; downgrade is intentionally a no-op
because these tables carried no live data and are no longer modelled anywhere.

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-06-06
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e3f4a5b6c7d8"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


# Order chosen so referencing tables drop before referenced ones; CASCADE makes
# the order non-critical, but we keep it explicit for readability.
DEAD_TABLES = [
    "agent_runs",
    "comparison_items",
    "comparison_metrics",
    "idea_comparisons",
    "roadmap_stages",
    "business_roadmaps",
    "embeddings",
    "experiments",
    "idea_metrics",
    "idea_versions",
    "agents",
]


def upgrade() -> None:
    for table in DEAD_TABLES:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')


def downgrade() -> None:
    # One-way cleanup: these tables held no live application data and are no
    # longer defined by any ORM model, so there is nothing meaningful to
    # recreate. Restore from the prior revision's models if ever needed.
    pass
