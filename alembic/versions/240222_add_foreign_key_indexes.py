"""Add indexes on foreign keys for performance optimization.

Revision ID: 240222_add_foreign_key_indexes
Revises: 239000f30fd1_sync_with_guid
Create Date: 2026-02-22 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '240222_add_foreign_key_indexes'
down_revision = '239000f30fd1_sync_with_guid'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create indexes on commonly queried foreign key columns."""
    
    # Agent-related indexes
    op.create_index('idx_agent_runs_stage_id', 'agent_runs', ['stage_id'])
    op.create_index('idx_agent_runs_agent_id', 'agent_runs', ['agent_id'])
    op.create_index('idx_validation_logs_agent_run_id', 'validation_logs', ['agent_run_id'])
    op.create_index('idx_embeddings_agent_id', 'embeddings', ['agent_id'])
    
    # Business-related indexes
    op.create_index('idx_businesses_owner_id', 'businesses', ['owner_id'])
    op.create_index('idx_business_roadmaps_business_id', 'business_roadmaps', ['business_id'])
    op.create_index('idx_roadmap_stages_roadmap_id', 'roadmap_stages', ['roadmap_id'])
    op.create_index('idx_business_collaborators_business_id', 'business_collaborators', ['business_id'])
    op.create_index('idx_business_collaborators_user_id', 'business_collaborators', ['user_id'])
    op.create_index('idx_business_invites_business_id', 'business_invites', ['business_id'])
    op.create_index('idx_business_invites_user_id', 'business_invites', ['user_id'])
    
    # Idea-related indexes
    op.create_index('idx_ideas_owner_id', 'ideas', ['owner_id'])
    op.create_index('idx_idea_versions_idea_id', 'idea_versions', ['idea_id'])
    op.create_index('idx_idea_accesses_idea_id', 'idea_accesses', ['idea_id'])
    op.create_index('idx_idea_accesses_user_id', 'idea_accesses', ['user_id'])
    op.create_index('idx_idea_metrics_idea_id', 'idea_metrics', ['idea_id'])
    op.create_index('idx_experiments_idea_id', 'experiments', ['idea_id'])
    
    # Billing-related indexes
    op.create_index('idx_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('idx_subscriptions_plan_id', 'subscriptions', ['plan_id'])
    op.create_index('idx_payments_subscription_id', 'payments', ['subscription_id'])
    op.create_index('idx_payment_methods_user_id', 'payment_methods', ['user_id'])
    op.create_index('idx_usages_user_id', 'usages', ['user_id'])
    
    # Chat-related indexes (note: actual table is chat_sessions, not chats)
    op.create_index('idx_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('idx_chat_sessions_business_id', 'chat_sessions', ['business_id'])
    op.create_index('idx_chat_sessions_idea_id', 'chat_sessions', ['idea_id'])
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['session_id'])
    
    # Partner-related indexes
    op.create_index('idx_partner_profiles_user_id', 'partner_profiles', ['user_id'])
    op.create_index('idx_partner_requests_sender_id', 'partner_requests', ['sender_id'])
    op.create_index('idx_partner_requests_receiver_id', 'partner_requests', ['receiver_id'])
    
    # Core-related indexes
    op.create_index('idx_files_owner_id', 'files', ['owner_id'])
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_share_links_created_by', 'share_links', ['created_by'])
    op.create_index('idx_share_links_business_id', 'share_links', ['business_id'])
    op.create_index('idx_share_links_idea_id', 'share_links', ['idea_id'])


def downgrade() -> None:
    """Drop all created indexes."""
    
    # Drop all indexes in reverse order
    op.drop_index('idx_share_links_idea_id', table_name='share_links')
    op.drop_index('idx_share_links_business_id', table_name='share_links')
    op.drop_index('idx_share_links_created_by', table_name='share_links')
    op.drop_index('idx_notifications_user_id', table_name='notifications')
    op.drop_index('idx_files_owner_id', table_name='files')
    op.drop_index('idx_partner_requests_receiver_id', table_name='partner_requests')
    op.drop_index('idx_partner_requests_sender_id', table_name='partner_requests')
    op.drop_index('idx_partner_profiles_user_id', table_name='partner_profiles')
    op.drop_index('idx_chat_messages_session_id', table_name='chat_messages')
    op.drop_index('idx_chat_sessions_idea_id', table_name='chat_sessions')
    op.drop_index('idx_chat_sessions_business_id', table_name='chat_sessions')
    op.drop_index('idx_chat_sessions_user_id', table_name='chat_sessions')
    op.drop_index('idx_usages_user_id', table_name='usages')
    op.drop_index('idx_payment_methods_user_id', table_name='payment_methods')
    op.drop_index('idx_payments_subscription_id', table_name='payments')
    op.drop_index('idx_subscriptions_plan_id', table_name='subscriptions')
    op.drop_index('idx_subscriptions_user_id', table_name='subscriptions')
    op.drop_index('idx_experiments_idea_id', table_name='experiments')
    op.drop_index('idx_idea_metrics_idea_id', table_name='idea_metrics')
    op.drop_index('idx_idea_accesses_user_id', table_name='idea_accesses')
    op.drop_index('idx_idea_accesses_idea_id', table_name='idea_accesses')
    op.drop_index('idx_idea_versions_idea_id', table_name='idea_versions')
    op.drop_index('idx_ideas_owner_id', table_name='ideas')
    op.drop_index('idx_business_invites_user_id', table_name='business_invites')
    op.drop_index('idx_business_invites_business_id', table_name='business_invites')
    op.drop_index('idx_business_collaborators_user_id', table_name='business_collaborators')
    op.drop_index('idx_business_collaborators_business_id', table_name='business_collaborators')
    op.drop_index('idx_roadmap_stages_roadmap_id', table_name='roadmap_stages')
    op.drop_index('idx_business_roadmaps_business_id', table_name='business_roadmaps')
    op.drop_index('idx_businesses_owner_id', table_name='businesses')
    op.drop_index('idx_embeddings_agent_id', table_name='embeddings')
    op.drop_index('idx_validation_logs_agent_run_id', table_name='validation_logs')
    op.drop_index('idx_agent_runs_agent_id', table_name='agent_runs')
    op.drop_index('idx_agent_runs_stage_id', table_name='agent_runs')
