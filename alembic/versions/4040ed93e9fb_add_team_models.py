"""add_team_models

Revision ID: 4040ed93e9fb
Revises: 25807a666483
Create Date: 2026-03-18 14:36:35.435703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4040ed93e9fb'
down_revision: Union[str, None] = '25807a666483'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('teams',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('role', sa.Enum('owner', 'editor', 'viewer', name='collaboratorrole'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('team_idea_access',
    sa.Column('team_id', sa.UUID(), nullable=False),
    sa.Column('idea_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['idea_id'], ['ideas.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('team_id', 'idea_id')
    )
    
    op.create_table('team_members',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('team_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('added_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('team_members')
    op.drop_table('team_idea_access')
    op.drop_table('teams')
