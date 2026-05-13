"""unify ai runs in agent_runs

Revision ID: d1f3a5c9b802
Revises: 671f027bd958
Create Date: 2026-05-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1f3a5c9b802'
down_revision: Union[str, None] = '671f027bd958'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


agent_ai_type_enum = sa.Enum(
    'BUSINESS_ROADMAP',
    'ROADMAP_STAGE',
    'CHAT_SESSION',
    'CHAT_MESSAGE',
    'IDEA_ANALYSIS',
    'IDEA_METRIC',
    'IDEA_COMPARISON',
    'COMPARISON_METRIC',
    'EXPERIMENT_RESULT',
    'VALIDATION_LOG',
    'GENERAL',
    name='agentaitype',
)


def upgrade() -> None:
    bind = op.get_bind()
    agent_ai_type_enum.create(bind, checkfirst=True)

    with op.batch_alter_table('agent_runs', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'ai_type',
                agent_ai_type_enum,
                nullable=False,
                server_default='ROADMAP_STAGE',
            )
        )
        batch_op.add_column(sa.Column('roadmap_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('chat_session_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('chat_message_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('idea_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('idea_metric_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('idea_comparison_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('comparison_item_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('comparison_metric_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('experiment_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('critique_json', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('threshold_passed', sa.Boolean(), nullable=True))
        batch_op.alter_column(
            'stage_id',
            existing_type=sa.UUID(),
            nullable=True,
            existing_nullable=False,
        )
        batch_op.alter_column(
            'agent_id',
            existing_type=sa.UUID(),
            nullable=True,
            existing_nullable=False,
        )
        batch_op.create_foreign_key(
            'fk_agent_runs_roadmap_id_business_roadmaps',
            'business_roadmaps',
            ['roadmap_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            'fk_agent_runs_chat_session_id_chat_sessions',
            'chat_sessions',
            ['chat_session_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            'fk_agent_runs_chat_message_id_chat_messages',
            'chat_messages',
            ['chat_message_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            'fk_agent_runs_idea_id_ideas',
            'ideas',
            ['idea_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            'fk_agent_runs_idea_metric_id_idea_metrics',
            'idea_metrics',
            ['idea_metric_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            'fk_agent_runs_idea_comparison_id_idea_comparisons',
            'idea_comparisons',
            ['idea_comparison_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            'fk_agent_runs_comparison_item_id_comparison_items',
            'comparison_items',
            ['comparison_item_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            'fk_agent_runs_comparison_metric_id_comparison_metrics',
            'comparison_metrics',
            ['comparison_metric_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            'fk_agent_runs_experiment_id_experiments',
            'experiments',
            ['experiment_id'],
            ['id'],
        )
        batch_op.create_index('ix_agent_runs_ai_type', ['ai_type'], unique=False)

    with op.batch_alter_table('agent_runs', schema=None) as batch_op:
        batch_op.alter_column('ai_type', server_default=None)

    op.execute(
        """
        UPDATE agent_runs
        SET
            critique_json = (
                SELECT validation_logs.critique_json
                FROM validation_logs
                WHERE validation_logs.agent_run_id = agent_runs.id
                ORDER BY validation_logs.created_at DESC
                LIMIT 1
            ),
            threshold_passed = (
                SELECT validation_logs.threshold_passed
                FROM validation_logs
                WHERE validation_logs.agent_run_id = agent_runs.id
                ORDER BY validation_logs.created_at DESC
                LIMIT 1
            ),
            confidence_score = COALESCE(
                (
                    SELECT validation_logs.confidence_score
                    FROM validation_logs
                    WHERE validation_logs.agent_run_id = agent_runs.id
                    ORDER BY validation_logs.created_at DESC
                    LIMIT 1
                ),
                confidence_score
            )
        WHERE EXISTS (
            SELECT 1
            FROM validation_logs
            WHERE validation_logs.agent_run_id = agent_runs.id
        )
        """
    )


def downgrade() -> None:
    with op.batch_alter_table('agent_runs', schema=None) as batch_op:
        batch_op.drop_index('ix_agent_runs_ai_type')
        batch_op.drop_constraint(
            'fk_agent_runs_chat_session_id_chat_sessions',
            type_='foreignkey',
        )
        batch_op.drop_constraint(
            'fk_agent_runs_chat_message_id_chat_messages',
            type_='foreignkey',
        )
        batch_op.drop_constraint(
            'fk_agent_runs_roadmap_id_business_roadmaps',
            type_='foreignkey',
        )
        batch_op.drop_constraint(
            'fk_agent_runs_experiment_id_experiments',
            type_='foreignkey',
        )
        batch_op.drop_constraint(
            'fk_agent_runs_comparison_metric_id_comparison_metrics',
            type_='foreignkey',
        )
        batch_op.drop_constraint(
            'fk_agent_runs_comparison_item_id_comparison_items',
            type_='foreignkey',
        )
        batch_op.drop_constraint(
            'fk_agent_runs_idea_comparison_id_idea_comparisons',
            type_='foreignkey',
        )
        batch_op.drop_constraint(
            'fk_agent_runs_idea_metric_id_idea_metrics',
            type_='foreignkey',
        )
        batch_op.drop_constraint(
            'fk_agent_runs_idea_id_ideas',
            type_='foreignkey',
        )
        batch_op.alter_column(
            'agent_id',
            existing_type=sa.UUID(),
            nullable=False,
            existing_nullable=True,
        )
        batch_op.alter_column(
            'stage_id',
            existing_type=sa.UUID(),
            nullable=False,
            existing_nullable=True,
        )
        batch_op.drop_column('threshold_passed')
        batch_op.drop_column('critique_json')
        batch_op.drop_column('experiment_id')
        batch_op.drop_column('comparison_metric_id')
        batch_op.drop_column('comparison_item_id')
        batch_op.drop_column('idea_comparison_id')
        batch_op.drop_column('idea_metric_id')
        batch_op.drop_column('idea_id')
        batch_op.drop_column('chat_message_id')
        batch_op.drop_column('chat_session_id')
        batch_op.drop_column('roadmap_id')
        batch_op.drop_column('ai_type')

    bind = op.get_bind()
    agent_ai_type_enum.drop(bind, checkfirst=True)
