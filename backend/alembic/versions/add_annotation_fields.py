"""Add page_number and content to annotations

Revision ID: add_annotation_fields
Revises: 29da2ef00ccd
Create Date: 2025-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_annotation_fields'
down_revision = '29da2ef00ccd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to annotations table
    op.add_column('annotations', sa.Column('page_number', sa.Integer(), server_default='1', nullable=True))
    op.add_column('annotations', sa.Column('annotation_type', sa.String(length=50), server_default='canvas', nullable=True))
    op.add_column('annotations', sa.Column('content', sa.Text(), nullable=True))
    
    # Make annotation_data nullable (was required before)
    op.alter_column('annotations', 'annotation_data',
                    existing_type=sa.Text(),
                    nullable=True)


def downgrade() -> None:
    op.drop_column('annotations', 'content')
    op.drop_column('annotations', 'annotation_type')
    op.drop_column('annotations', 'page_number')
    
    op.alter_column('annotations', 'annotation_data',
                    existing_type=sa.Text(),
                    nullable=False)
