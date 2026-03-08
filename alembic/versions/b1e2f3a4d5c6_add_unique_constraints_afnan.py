"""add_unique_constraints_afnan

Applies unique constraints across all tables following Afnan's review.
Prevents duplicate data at the database level for all junction and
domain tables.

Revision ID: b1e2f3a4d5c6
Revises: a9ff7c1f6f12
Create Date: 2026-03-05 21:52:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b1e2f3a4d5c6'
down_revision: Union[str, None] = 'a9ff7c1f6f12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # business_collaborators
    # Prevent the same user being added to the same business twice
    # ----------------------------------------------------------------
    op.create_unique_constraint(
        'uq_business_collaborator_business_user',
        'business_collaborators',
        ['business_id', 'user_id'],
    )

    # ----------------------------------------------------------------
    # business_invite_ideas
    # Prevent the same idea being listed in the same invite twice
    # ----------------------------------------------------------------
    op.create_unique_constraint(
        'uq_business_invite_idea_invite_idea',
        'business_invite_ideas',
        ['invite_id', 'idea_id'],
    )

    # ----------------------------------------------------------------
    # comparison_items
    # Prevent the same idea appearing twice in the same comparison
    # ----------------------------------------------------------------
    op.create_unique_constraint(
        'uq_comparison_item_comparison_idea',
        'comparison_items',
        ['comparison_id', 'idea_id'],
    )

    # ----------------------------------------------------------------
    # comparison_metrics
    # Prevent the same metric name appearing twice in a comparison
    # ----------------------------------------------------------------
    op.create_unique_constraint(
        'uq_comparison_metric_comparison_name',
        'comparison_metrics',
        ['comparison_id', 'metric_name'],
    )

    # ----------------------------------------------------------------
    # idea_metrics
    # Prevent duplicate metric names per idea
    # ----------------------------------------------------------------
    op.create_unique_constraint(
        'uq_idea_metric_idea_name',
        'idea_metrics',
        ['idea_id', 'name'],
    )

    # ----------------------------------------------------------------
    # idea_accesses
    # Prevent duplicate access records for the same user/idea pair
    # ----------------------------------------------------------------
    op.create_unique_constraint(
        'uq_idea_access_idea_user',
        'idea_accesses',
        ['idea_id', 'user_id'],
    )

    # ----------------------------------------------------------------
    # partner_profiles
    # Each user can have only one partner profile
    # ----------------------------------------------------------------
    op.create_unique_constraint(
        'uq_partner_profile_user',
        'partner_profiles',
        ['user_id'],
    )

    # ----------------------------------------------------------------
    # partner_requests
    # Prevent a partner from being requested more than once per business
    # ----------------------------------------------------------------
    op.create_unique_constraint(
        'uq_partner_request_business_partner',
        'partner_requests',
        ['business_id', 'partner_id'],
    )

    # ----------------------------------------------------------------
    # usages
    # Each user has exactly one usage row per resource type
    # ----------------------------------------------------------------
    op.create_unique_constraint(
        'uq_usage_user_resource_type',
        'usages',
        ['user_id', 'resource_type'],
    )


def downgrade() -> None:
    # Remove all unique constraints in reverse order

    op.drop_constraint('uq_usage_user_resource_type', 'usages', type_='unique')
    op.drop_constraint('uq_partner_request_business_partner', 'partner_requests', type_='unique')
    op.drop_constraint('uq_partner_profile_user', 'partner_profiles', type_='unique')
    op.drop_constraint('uq_idea_access_idea_user', 'idea_accesses', type_='unique')
    op.drop_constraint('uq_idea_metric_idea_name', 'idea_metrics', type_='unique')
    op.drop_constraint('uq_comparison_metric_comparison_name', 'comparison_metrics', type_='unique')
    op.drop_constraint('uq_comparison_item_comparison_idea', 'comparison_items', type_='unique')
    op.drop_constraint('uq_business_invite_idea_invite_idea', 'business_invite_ideas', type_='unique')
    op.drop_constraint('uq_business_collaborator_business_user', 'business_collaborators', type_='unique')
