"""add_foreign_key_indexes

Revision ID: add_foreign_key_indexes
Revises: 240222_add_foreign_key_indexes
Create Date: 2026-02-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_foreign_key_indexes'
down_revision = '240222_add_foreign_key_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes on foreign keys for improved query performance."""
    
    # Ideas table
    op.create_index('ix_ideas_owner_id', 'ideas', ['owner_id'])
    op.create_index('ix_ideas_business_id', 'ideas', ['business_id'])
    
    # Idea versions
    op.create_index('ix_idea_versions_idea_id', 'idea_versions', ['idea_id'])
    
    # Idea metrics
    op.create_index('ix_idea_metrics_idea_id', 'idea_metrics', ['idea_id'])
    
    # Experiments
    op.create_index('ix_experiments_idea_id', 'experiments', ['idea_id'])
    
    # Comparisons
    op.create_index('ix_idea_comparisons_idea_id', 'idea_comparisons', ['idea_id'])
    
    # Business collaborators
    op.create_index('ix_business_collaborators_business_id', 'business_collaborators', ['business_id'])
    op.create_index('ix_business_collaborators_user_id', 'business_collaborators', ['user_id'])
    
    # Business invites
    op.create_index('ix_business_invites_business_id', 'business_invites', ['business_id'])
    op.create_index('ix_business_invites_invited_by', 'business_invites', ['invited_by'])
    
    # Business invite ideas
    op.create_index('ix_business_invite_ideas_invite_id', 'business_invite_ideas', ['invite_id'])
    op.create_index('ix_business_invite_ideas_idea_id', 'business_invite_ideas', ['idea_id'])
    
    # Roadmap stages
    op.create_index('ix_roadmap_stages_roadmap_id', 'roadmap_stages', ['roadmap_id'])
    
    # Chat sessions
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('ix_chat_sessions_idea_id', 'chat_sessions', ['idea_id'])
    op.create_index('ix_chat_sessions_business_id', 'chat_sessions', ['business_id'])
    
    # Chat messages
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_user_id', 'chat_messages', ['user_id'])
    
    # Payments
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_subscription_id', 'payments', ['subscription_id'])
    op.create_index('ix_payments_payment_method_id', 'payments', ['payment_method_id'])
    
    # Subscriptions
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('ix_subscriptions_plan_id', 'subscriptions', ['plan_id'])
    
    # Payment methods
    op.create_index('ix_payment_methods_user_id', 'payment_methods', ['user_id'])
    
    # Usage
    op.create_index('ix_usage_user_id', 'usage', ['user_id'])
    
    # Partner requests
    op.create_index('ix_partner_requests_business_id', 'partner_requests', ['business_id'])
    op.create_index('ix_partner_requests_partner_id', 'partner_requests', ['partner_id'])
    
    # Embeddings
    op.create_index('ix_embeddings_business_id', 'embeddings', ['business_id'])
    op.create_index('ix_embeddings_user_id', 'embeddings', ['user_id'])
    
    # Idea access
    op.create_index('ix_idea_accesses_idea_id', 'idea_accesses', ['idea_id'])
    op.create_index('ix_idea_accesses_user_id', 'idea_accesses', ['user_id'])
    op.create_index('ix_idea_accesses_business_id', 'idea_accesses', ['business_id'])
    
    # Share links
    op.create_index('ix_share_links_idea_id', 'share_links', ['idea_id'])
    op.create_index('ix_share_links_business_id', 'share_links', ['business_id'])
    op.create_index('ix_share_links_created_by', 'share_links', ['created_by'])
    
    # Agent runs
    op.create_index('ix_agent_runs_stage_id', 'agent_runs', ['stage_id'])
    op.create_index('ix_agent_runs_agent_id', 'agent_runs', ['agent_id'])
    
    # Validation logs
    op.create_index('ix_validation_logs_agent_id', 'validation_logs', ['agent_id'])


def downgrade() -> None:
    """Remove all foreign key indexes."""
    
    # Drop all indexes
    op.drop_index('ix_ideas_owner_id', table_name='ideas')
    op.drop_index('ix_ideas_business_id', table_name='ideas')
    op.drop_index('ix_idea_versions_idea_id', table_name='idea_versions')
    op.drop_index('ix_idea_metrics_idea_id', table_name='idea_metrics')
    op.drop_index('ix_experiments_idea_id', table_name='experiments')
    op.drop_index('ix_idea_comparisons_idea_id', table_name='idea_comparisons')
    op.drop_index('ix_business_collaborators_business_id', table_name='business_collaborators')
    op.drop_index('ix_business_collaborators_user_id', table_name='business_collaborators')
    op.drop_index('ix_business_invites_business_id', table_name='business_invites')
    op.drop_index('ix_business_invites_invited_by', table_name='business_invites')
    op.drop_index('ix_business_invite_ideas_invite_id', table_name='business_invite_ideas')
    op.drop_index('ix_business_invite_ideas_idea_id', table_name='business_invite_ideas')
    op.drop_index('ix_roadmap_stages_roadmap_id', table_name='roadmap_stages')
    op.drop_index('ix_chat_sessions_user_id', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_idea_id', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_business_id', table_name='chat_sessions')
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_user_id', table_name='chat_messages')
    op.drop_index('ix_payments_user_id', table_name='payments')
    op.drop_index('ix_payments_subscription_id', table_name='payments')
    op.drop_index('ix_payments_payment_method_id', table_name='payments')
    op.drop_index('ix_subscriptions_user_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_plan_id', table_name='subscriptions')
    op.drop_index('ix_payment_methods_user_id', table_name='payment_methods')
    op.drop_index('ix_usage_user_id', table_name='usage')
    op.drop_index('ix_partner_requests_business_id', table_name='partner_requests')
    op.drop_index('ix_partner_requests_partner_id', table_name='partner_requests')
    op.drop_index('ix_embeddings_business_id', table_name='embeddings')
    op.drop_index('ix_embeddings_user_id', table_name='embeddings')
    op.drop_index('ix_idea_accesses_idea_id', table_name='idea_accesses')
    op.drop_index('ix_idea_accesses_user_id', table_name='idea_accesses')
    op.drop_index('ix_idea_accesses_business_id', table_name='idea_accesses')
    op.drop_index('ix_share_links_idea_id', table_name='share_links')
    op.drop_index('ix_share_links_business_id', table_name='share_links')
    op.drop_index('ix_share_links_created_by', table_name='share_links')
    op.drop_index('ix_agent_runs_stage_id', table_name='agent_runs')
    op.drop_index('ix_agent_runs_agent_id', table_name='agent_runs')
    op.drop_index('ix_validation_logs_agent_id', table_name='validation_logs')
