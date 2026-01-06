"""add user_id to documents

Revision ID: 0004_add_user_id_to_documents
Revises: 0003_add_user_id
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_add_user_id_to_documents'
down_revision = '0003_add_user_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('documents') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(36), nullable=True))
        batch_op.create_foreign_key('fk_documents_user_id', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('documents') as batch_op:
        batch_op.drop_constraint('fk_documents_user_id', type_='foreignkey')
        batch_op.drop_column('user_id')
