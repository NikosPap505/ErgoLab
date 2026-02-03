"""rename_audit_user_email_to_hash

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-03 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('audit_logs', 'user_email', new_column_name='user_email_hash')
    # Hash existing email values (use appropriate hash function for your use case)
    op.execute("""
        UPDATE audit_logs 
        SET user_email_hash = encode(sha256(user_email_hash::bytea), 'hex')
        WHERE user_email_hash IS NOT NULL
    """)


def downgrade():
    op.alter_column('audit_logs', 'user_email_hash', new_column_name='user_email')
