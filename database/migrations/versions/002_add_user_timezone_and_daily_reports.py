"""Add timezone and daily_reports_enabled to users

Revision ID: 002
Revises: 001
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add timezone column with default 'UTC'
    op.add_column('users', sa.Column('timezone', sa.String(length=64), nullable=False, server_default='UTC'))
    
    # Add daily_reports_enabled column with default True
    op.add_column('users', sa.Column('daily_reports_enabled', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    op.drop_column('users', 'daily_reports_enabled')
    op.drop_column('users', 'timezone')
