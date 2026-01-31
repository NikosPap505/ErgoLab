"""add_analytics_tables

Revision ID: add_analytics_tables
Revises: add_thumbnail_path
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_analytics_tables'
down_revision = 'add_thumbnail_path'
branch_labels = None
depends_on = None


def upgrade():
    # Cost tracking table
    op.create_table(
        'cost_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_cost', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_cost_tracking_project', 'cost_tracking', ['project_id'])
    op.create_index('idx_cost_tracking_material', 'cost_tracking', ['material_id'])
    op.create_index('idx_cost_tracking_date', 'cost_tracking', ['transaction_date'])
    
    # Budgets table
    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('total_budget', sa.Float(), nullable=False),
        sa.Column('materials_budget', sa.Float(), nullable=False),
        sa.Column('labor_budget', sa.Float(), nullable=False),
        sa.Column('other_budget', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )
    
    # Material usage trends table
    op.create_table(
        'material_usage_trends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer()),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('total_quantity', sa.Integer(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('avg_daily_usage', sa.Float()),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trends_material', 'material_usage_trends', ['material_id'])
    op.create_index('idx_trends_period', 'material_usage_trends', ['period_start', 'period_end'])
    
    # Alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='warning'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.String(50)),
        sa.Column('entity_id', sa.Integer()),
        sa.Column('is_read', sa.Integer(), server_default='0'),
        sa.Column('is_resolved', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('resolved_by', sa.Integer()),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alerts_type', 'alerts', ['alert_type'])
    op.create_index('idx_alerts_severity', 'alerts', ['severity'])
    op.create_index('idx_alerts_entity', 'alerts', ['entity_type', 'entity_id'])
    op.create_index('idx_alerts_unresolved', 'alerts', ['is_resolved'])
    
    # Add is_active column to materials if not exists
    try:
        op.add_column('materials', sa.Column('is_active', sa.Integer(), server_default='1'))
    except Exception:
        pass  # Column might already exist


def downgrade():
    op.drop_index('idx_alerts_unresolved')
    op.drop_index('idx_alerts_entity')
    op.drop_index('idx_alerts_severity')
    op.drop_index('idx_alerts_type')
    op.drop_table('alerts')
    
    op.drop_index('idx_trends_period')
    op.drop_index('idx_trends_material')
    op.drop_table('material_usage_trends')
    
    op.drop_table('budgets')
    
    op.drop_index('idx_cost_tracking_date')
    op.drop_index('idx_cost_tracking_material')
    op.drop_index('idx_cost_tracking_project')
    op.drop_table('cost_tracking')
    
    try:
        op.drop_column('materials', 'is_active')
    except Exception:
        pass
