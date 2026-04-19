"""Fix documents and files schema to match models

Revision ID: 0002_fix_documents_files_schema
Revises: a3b7c9d12e45
Create Date: 2026-04-20 00:00:00.000000
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002_fix_documents_files_schema'
down_revision: Union[str, None] = 'a3b7c9d12e45'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop FK constraint from tasks first
    op.drop_constraint('tasks_document_id_fkey', 'tasks', type_='foreignkey')

    # Drop old tables (no data yet)
    op.drop_table('documents')
    op.drop_table('files')

    # Recreate files with correct schema
    op.create_table('files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('storage_backend', sa.String(50), nullable=True),
        sa.Column('thumbnail_path', sa.String(500), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('ocr_language', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_files_user_id', 'files', ['user_id'])
    op.create_index('ix_files_checksum', 'files', ['checksum'])

    # Recreate documents with correct schema
    op.create_table('documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('doc_metadata', sa.JSON(), nullable=True),
        sa.Column('processing_status', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    op.create_index('ix_documents_type', 'documents', ['type'])
    op.create_index('ix_documents_processing_status', 'documents', ['processing_status'])
    op.create_index('ix_documents_uploaded_at', 'documents', ['uploaded_at'])

    # Fix tasks.document_id FK (references documents which was recreated)
    op.drop_constraint('tasks_document_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key(
        'tasks_document_id_fkey', 'tasks', 'documents',
        ['document_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    pass
