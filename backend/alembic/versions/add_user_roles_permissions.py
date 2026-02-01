"""add user roles and permissions

Revision ID: add_user_roles_permissions
Revises: add_notification_preferences
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_user_roles_permissions"
down_revision = "add_notification_preferences"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE TEXT USING role::text")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute(
        "CREATE TYPE userrole AS ENUM ('admin', 'manager', 'supervisor', 'worker', 'viewer')"
    )

    op.execute("UPDATE users SET role='admin' WHERE role='ADMIN'")
    op.execute("UPDATE users SET role='manager' WHERE role='MANAGER'")
    op.execute("UPDATE users SET role='supervisor' WHERE role='SUPERVISOR'")
    op.execute("UPDATE users SET role='worker' WHERE role IN ('FIELD_WORKER', 'field_worker')")
    op.execute("UPDATE users SET role='viewer' WHERE role IN ('CONTRACTOR', 'contractor')")

    op.alter_column(
        "users",
        "role",
        type_=postgresql.ENUM(
            "admin",
            "manager",
            "supervisor",
            "worker",
            "viewer",
            name="userrole",
        ),
        nullable=False,
        server_default="worker",
        postgresql_using="role::userrole",
    )

    op.add_column("users", sa.Column("is_superuser", sa.Boolean(), server_default=sa.false()))
    op.add_column("users", sa.Column("address", sa.String(), nullable=True))
    op.add_column("users", sa.Column("last_login", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("users", "last_login")
    op.drop_column("users", "address")
    op.drop_column("users", "is_superuser")

    op.execute("ALTER TABLE users ALTER COLUMN role TYPE TEXT USING role::text")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute(
        "CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'FIELD_WORKER', 'CONTRACTOR')"
    )

    op.execute("UPDATE users SET role='ADMIN' WHERE role='admin'")
    op.execute("UPDATE users SET role='MANAGER' WHERE role='manager'")
    op.execute("UPDATE users SET role='FIELD_WORKER' WHERE role IN ('worker', 'supervisor')")
    op.execute("UPDATE users SET role='CONTRACTOR' WHERE role='viewer'")

    op.alter_column(
        "users",
        "role",
        type_=postgresql.ENUM(
            "ADMIN",
            "MANAGER",
            "FIELD_WORKER",
            "CONTRACTOR",
            name="userrole",
        ),
        nullable=True,
        postgresql_using="role::userrole",
    )
