"""add team approval flow manually

Revision ID: 3290267b6423
Revises: 0ab04a574cb4
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3290267b6423'
down_revision = '0ab04a574cb4'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create business_join_requests table only if it doesn't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'business_join_requests' not in tables:
        op.create_table('business_join_requests',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('business_id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # 2. Add columns to business_invites
    columns_invites = [c['name'] for c in inspector.get_columns('business_invites')]
    with op.batch_alter_table('business_invites', schema=None) as batch_op:
        if 'idea_id' not in columns_invites:
            batch_op.add_column(sa.Column('idea_id', sa.UUID(), nullable=True))
        if 'requires_approval' not in columns_invites:
            batch_op.add_column(sa.Column('requires_approval', sa.Boolean(), nullable=True, server_default='1'))
    
    # 3. Add column to business_collaborators
    columns_collaborators = [c['name'] for c in inspector.get_columns('business_collaborators')]
    with op.batch_alter_table('business_collaborators', schema=None) as batch_op:
        if 'idea_id' not in columns_collaborators:
            batch_op.add_column(sa.Column('idea_id', sa.UUID(), nullable=True))


def downgrade():
    op.drop_table('business_join_requests')
    with op.batch_alter_table('business_collaborators', schema=None) as batch_op:
        batch_op.drop_column('idea_id')
    with op.batch_alter_table('business_invites', schema=None) as batch_op:
        batch_op.drop_column('requires_approval')
        batch_op.drop_column('idea_id')
