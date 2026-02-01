"""add_performance_indexes

Revision ID: performance_indexes_001
Revises: add_annotation_fields
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'performance_indexes_001'
down_revision = 'add_annotation_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Create performance indexes for all major tables"""
    
    # Users table indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=False, if_not_exists=True)
    op.create_index('idx_users_is_active', 'users', ['is_active'], if_not_exists=True)
    
    # Materials table indexes
    op.create_index('idx_materials_sku', 'materials', ['sku'], if_not_exists=True)
    op.create_index('idx_materials_category', 'materials', ['category'], if_not_exists=True)
    op.create_index('idx_materials_barcode', 'materials', ['barcode'], if_not_exists=True)
    
    # Projects table indexes
    op.create_index('idx_projects_code', 'projects', ['code'], if_not_exists=True)
    op.create_index('idx_projects_status', 'projects', ['status'], if_not_exists=True)
    op.create_index('idx_projects_dates', 'projects', ['start_date', 'end_date'], if_not_exists=True)
    
    # Warehouses table indexes
    op.create_index('idx_warehouses_code', 'warehouses', ['code'], if_not_exists=True)
    op.create_index('idx_warehouses_project', 'warehouses', ['project_id'], if_not_exists=True)
    op.create_index('idx_warehouses_central', 'warehouses', ['is_central'], if_not_exists=True)
    
    # Inventory table indexes (composite already exists as unique_warehouse_material)
    op.create_index('idx_inventory_low_stock', 'inventory_stocks', 
                    ['warehouse_id', 'quantity'], if_not_exists=True)
    
    # Stock transactions indexes
    # Note: Individual indexes on warehouse_id, material_id, and created_at allow queries on any single column
    # Composite index allows efficient queries combining these columns in order (warehouse_id, material_id, created_at)
    op.create_index('idx_transactions_warehouse', 'stock_transactions', ['warehouse_id'], if_not_exists=True)
    op.create_index('idx_transactions_material', 'stock_transactions', ['material_id'], if_not_exists=True)
    op.create_index('idx_transactions_type', 'stock_transactions', ['transaction_type'], if_not_exists=True)
    op.create_index('idx_transactions_date', 'stock_transactions', ['created_at'], if_not_exists=True)
    op.create_index('idx_transactions_composite', 'stock_transactions', 
                    ['warehouse_id', 'material_id', 'created_at'], if_not_exists=True)
    
    # Transfers table indexes
    op.create_index('idx_transfers_from', 'transfers', ['from_warehouse_id'], if_not_exists=True)
    op.create_index('idx_transfers_to', 'transfers', ['to_warehouse_id'], if_not_exists=True)
    op.create_index('idx_transfers_status', 'transfers', ['status'], if_not_exists=True)
    op.create_index('idx_transfers_date', 'transfers', ['created_at'], if_not_exists=True)
    
    # Documents table indexes
    op.create_index('idx_documents_project', 'documents', ['project_id'], if_not_exists=True)
    op.create_index('idx_documents_type', 'documents', ['file_type'], if_not_exists=True)
    op.create_index('idx_documents_uploaded', 'documents', ['uploaded_at'], if_not_exists=True)
    
    # Annotations table indexes
    op.create_index('idx_annotations_document', 'annotations', ['document_id'], if_not_exists=True)
    op.create_index('idx_annotations_user', 'annotations', ['created_by_id'], if_not_exists=True)


def downgrade():
    """Drop all performance indexes in reverse order"""
    
    # Annotations indexes
    op.drop_index('idx_annotations_user', table_name='annotations', if_exists=True)
    op.drop_index('idx_annotations_document', table_name='annotations', if_exists=True)
    
    # Documents indexes
    op.drop_index('idx_documents_uploaded', table_name='documents', if_exists=True)
    op.drop_index('idx_documents_type', table_name='documents', if_exists=True)
    op.drop_index('idx_documents_project', table_name='documents', if_exists=True)
    
    # Transfers indexes
    op.drop_index('idx_transfers_date', table_name='transfers', if_exists=True)
    op.drop_index('idx_transfers_status', table_name='transfers', if_exists=True)
    op.drop_index('idx_transfers_to', table_name='transfers', if_exists=True)
    op.drop_index('idx_transfers_from', table_name='transfers', if_exists=True)
    
    # Stock transactions indexes
    op.drop_index('idx_transactions_composite', table_name='stock_transactions', if_exists=True)
    op.drop_index('idx_transactions_date', table_name='stock_transactions', if_exists=True)
    op.drop_index('idx_transactions_type', table_name='stock_transactions', if_exists=True)
    op.drop_index('idx_transactions_material', table_name='stock_transactions', if_exists=True)
    op.drop_index('idx_transactions_warehouse', table_name='stock_transactions', if_exists=True)
    
    # Inventory indexes
    op.drop_index('idx_inventory_low_stock', table_name='inventory_stocks', if_exists=True)
    
    # Warehouses indexes
    op.drop_index('idx_warehouses_central', table_name='warehouses', if_exists=True)
    op.drop_index('idx_warehouses_project', table_name='warehouses', if_exists=True)
    op.drop_index('idx_warehouses_code', table_name='warehouses', if_exists=True)
    
    # Projects indexes
    op.drop_index('idx_projects_dates', table_name='projects', if_exists=True)
    op.drop_index('idx_projects_status', table_name='projects', if_exists=True)
    op.drop_index('idx_projects_code', table_name='projects', if_exists=True)
    
    # Materials indexes
    op.drop_index('idx_materials_barcode', table_name='materials', if_exists=True)
    op.drop_index('idx_materials_category', table_name='materials', if_exists=True)
    op.drop_index('idx_materials_sku', table_name='materials', if_exists=True)
    
    # Users indexes
    op.drop_index('idx_users_is_active', table_name='users', if_exists=True)
    op.drop_index('idx_users_email', table_name='users', if_exists=True)
