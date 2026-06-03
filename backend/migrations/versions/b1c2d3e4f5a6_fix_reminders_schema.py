"""Fix reminders table schema: align with current model

Revision ID: b1c2d3e4f5a6
Revises: a3b7c9d12e45
Create Date: 2026-06-03

"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '0002_fix_documents_files_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # remind_at → trigger_at
    op.alter_column('reminders', 'remind_at', new_column_name='trigger_at')
    op.drop_index('ix_reminders_remind_at', table_name='reminders')
    op.create_index('ix_reminders_trigger_at', 'reminders', ['trigger_at'])

    # user_id Spalte + FK entfernen (nicht im Model)
    op.drop_index('ix_reminders_user_id', table_name='reminders')
    op.drop_constraint('reminders_user_id_fkey', 'reminders', type_='foreignkey')
    op.drop_column('reminders', 'user_id')

    # Neue Spalten hinzufügen
    op.add_column('reminders', sa.Column('channels', sa.JSON(), nullable=True))
    op.add_column('reminders', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('reminders', sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
    op.add_column('reminders', sa.Column('snoozed_until', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('reminders', 'snoozed_until')
    op.drop_column('reminders', 'acknowledged_at')
    op.drop_column('reminders', 'error_message')
    op.drop_column('reminders', 'channels')

    op.add_column('reminders', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('reminders_user_id_fkey', 'reminders', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_reminders_user_id', 'reminders', ['user_id'])

    op.drop_index('ix_reminders_trigger_at', table_name='reminders')
    op.alter_column('reminders', 'trigger_at', new_column_name='remind_at')
    op.create_index('ix_reminders_remind_at', 'reminders', ['remind_at'])
