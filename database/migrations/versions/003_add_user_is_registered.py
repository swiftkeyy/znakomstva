"""Add is_registered to users

Revision ID: 003
Revises: 002
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_registered column with default False
    op.add_column('users', sa.Column('is_registered', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('users', 'is_registered')
