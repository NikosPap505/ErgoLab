"""add_thumbnail_path to documents

Revision ID: add_thumbnail_path
Revises: performance_indexes_001
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_thumbnail_path'
down_revision = 'performance_indexes_001'
branch_labels = None
depends_on = None


def upgrade():
    """Add thumbnail_path column to documents table"""
    op.add_column(
        'documents',
        sa.Column('thumbnail_path', sa.String(500), nullable=True)
    )


def downgrade():
    """Remove thumbnail_path column from documents table"""
    op.drop_column('documents', 'thumbnail_path')
