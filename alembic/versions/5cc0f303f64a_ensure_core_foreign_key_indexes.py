"""ensure core foreign-key indexes

Revision ID: 5cc0f303f64a
Revises: 54033c1a85e8
Create Date: 2026-02-26 08:31:55.718626

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5cc0f303f64a'
down_revision: Union[str, None] = '54033c1a85e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure critical FK/search indexes exist (safe across Postgres/SQLite).
    # We use raw SQL so the migration is idempotent across environments.

    # Canonical FK indexes (ix_*)
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_user_id ON payments (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_subscription_id ON payments (subscription_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_payments_payment_method_id ON payments (payment_method_id)")

    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id ON subscriptions (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_plan_id ON subscriptions (plan_id)")

    op.execute("CREATE INDEX IF NOT EXISTS ix_payment_methods_user_id ON payment_methods (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_usages_user_id ON usages (user_id)")

    op.execute("CREATE INDEX IF NOT EXISTS ix_ideas_owner_id ON ideas (owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ideas_business_id ON ideas (business_id)")

    op.execute("CREATE INDEX IF NOT EXISTS ix_idea_accesses_idea_id ON idea_accesses (idea_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_idea_accesses_user_id ON idea_accesses (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_idea_accesses_business_id ON idea_accesses (business_id)")

    # High-impact composite indexes used by hot-path queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_usages_user_id_resource_type "
        "ON usages (user_id, resource_type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_payments_user_id_created_at "
        "ON payments (user_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ideas_owner_id_created_at "
        "ON ideas (owner_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_idea_accesses_idea_id_user_id "
        "ON idea_accesses (idea_id, user_id)"
    )

    # Cleanup: drop older duplicate indexes (idx_*) if they exist.
    op.execute("DROP INDEX IF EXISTS idx_payments_subscription_id")
    op.execute("DROP INDEX IF EXISTS idx_subscriptions_user_id")
    op.execute("DROP INDEX IF EXISTS idx_subscriptions_plan_id")
    op.execute("DROP INDEX IF EXISTS idx_payment_methods_user_id")
    op.execute("DROP INDEX IF EXISTS idx_usages_user_id")
    op.execute("DROP INDEX IF EXISTS idx_ideas_owner_id")
    op.execute("DROP INDEX IF EXISTS idx_idea_accesses_idea_id")
    op.execute("DROP INDEX IF EXISTS idx_idea_accesses_user_id")
    op.execute("DROP INDEX IF EXISTS idx_idea_versions_idea_id")


def downgrade() -> None:
    # Best-effort rollback: drop composite indexes we added,
    # and restore legacy idx_* names (without removing ix_*).
    op.execute("DROP INDEX IF EXISTS ix_idea_accesses_idea_id_user_id")
    op.execute("DROP INDEX IF EXISTS ix_ideas_owner_id_created_at")
    op.execute("DROP INDEX IF EXISTS ix_payments_user_id_created_at")
    op.execute("DROP INDEX IF EXISTS ix_usages_user_id_resource_type")

    op.execute("CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON payments (subscription_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_id ON subscriptions (plan_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id ON payment_methods (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_usages_user_id ON usages (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ideas_owner_id ON ideas (owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_idea_accesses_idea_id ON idea_accesses (idea_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_idea_accesses_user_id ON idea_accesses (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_idea_versions_idea_id ON idea_versions (idea_id)")
