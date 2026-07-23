"""add api_key to users

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('api_key', sa.String(64), nullable=True))
    op.create_unique_constraint('uq_users_api_key', 'users', ['api_key'])
    op.create_index('ix_users_api_key', 'users', ['api_key'])


def downgrade() -> None:
    op.drop_index('ix_users_api_key', 'users')
    op.drop_constraint('uq_users_api_key', 'users', type_='unique')
    op.drop_column('users', 'api_key')
