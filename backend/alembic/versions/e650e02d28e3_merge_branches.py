"""merge_branches

Revision ID: e650e02d28e3
Revises: add_user_roles_permissions, add_reports_system
Create Date: 2026-02-01 11:48:30.243766

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e650e02d28e3'
down_revision = ('add_user_roles_permissions', 'add_reports_system')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
