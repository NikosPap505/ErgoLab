"""add_notification_preferences

Revision ID: add_notification_preferences
Revises: add_thumbnail_path
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_notification_preferences"
down_revision = "add_thumbnail_path"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email_low_stock", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("email_daily_reports", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("email_issue_assigned", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("email_budget_alerts", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("push_low_stock", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("push_daily_reports", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("push_issue_assigned", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("push_budget_alerts", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "idx_notification_prefs_user",
        "notification_preferences",
        ["user_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade():
    op.drop_index("idx_notification_prefs_user", table_name="notification_preferences", if_exists=True)
    op.drop_table("notification_preferences")
