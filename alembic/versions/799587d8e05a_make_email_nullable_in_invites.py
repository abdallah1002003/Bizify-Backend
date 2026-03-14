"""make_email_nullable_in_invites

Revision ID: 799587d8e05a
Revises: 4220423d4437
Create Date: 2026-03-14 01:48:37.924654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '799587d8e05a'
down_revision: Union[str, None] = '4220423d4437'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # UC_08/09: Make email nullable in business_invites
    with op.batch_alter_table('business_invites', schema=None) as batch_op:
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('business_invites', schema=None) as batch_op:
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(),
               nullable=False)
