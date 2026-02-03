"""add_account_lockout_fields

Revision ID: 982a64a68031
Revises: b9f3a1c7d2e4
Create Date: 2026-02-03 21:54:57.398216

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '982a64a68031'
down_revision = 'b9f3a1c7d2e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add account lockout fields to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
