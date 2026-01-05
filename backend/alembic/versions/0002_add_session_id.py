"""add session_id to conversations

Revision ID: 0002_add_session_id
Revises: 0001_initial
Create Date: 2026-01-04
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_session_id'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('session_id', sa.String(36), nullable=True))
    op.create_index(op.f('ix_conversations_session_id'), 'conversations', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_conversations_session_id'), table_name='conversations')
    op.drop_column('conversations', 'session_id')
