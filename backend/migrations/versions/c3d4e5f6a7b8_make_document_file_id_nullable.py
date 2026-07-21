"""Make documents.file_id nullable for Paperless-ngx imports

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-07-21

"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('documents', 'file_id', nullable=True)


def downgrade() -> None:
    op.alter_column('documents', 'file_id', nullable=False)
