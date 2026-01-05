"""add user_id to conversations

Revision ID: 0003_add_user_id
Revises: 0002_add_session_id
Create Date: 2026-01-04
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_user_id'
down_revision = '0002_add_session_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('conversations') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(36), nullable=True))
        batch_op.create_foreign_key('fk_conversations_user_id', 'users', ['user_id'], ['id'])
        batch_op.add_column(sa.Column('is_guest', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    with op.batch_alter_table('conversations') as batch_op:
        batch_op.drop_column('is_guest')
        batch_op.drop_constraint('fk_conversations_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
