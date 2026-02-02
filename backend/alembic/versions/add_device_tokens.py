"""add device tokens table

Revision ID: add_device_tokens
Revises: add_notification_preferences
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_device_tokens"
down_revision = "add_notification_preferences"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("device_type", sa.String()),
        sa.Column("device_name", sa.String()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_index("idx_device_tokens_token", "device_tokens", ["token"], unique=True)
    op.create_index("idx_device_tokens_user_id", "device_tokens", ["user_id"], unique=False)


def downgrade():
    op.drop_index("idx_device_tokens_user_id", table_name="device_tokens", if_exists=True)
    op.drop_index("idx_device_tokens_token", table_name="device_tokens", if_exists=True)
    op.drop_table("device_tokens")
