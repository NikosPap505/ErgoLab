"""add reports system tables

Revision ID: add_reports_system
Revises: add_analytics_tables
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_reports_system'
down_revision = 'add_analytics_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Daily Reports table
    op.create_table(
        'daily_reports',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False, index=True),
        
        # Καιρικές συνθήκες
        sa.Column('weather_condition', sa.Enum('SUNNY', 'CLOUDY', 'RAINY', 'STORMY', 'WINDY', 'SNOW', 'FOG', name='weathercondition'), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('weather_notes', sa.Text(), nullable=True),
        
        # Εργατικό δυναμικό
        sa.Column('workers_count', sa.Integer(), default=0),
        sa.Column('workers_present', sa.Text(), nullable=True),
        sa.Column('workers_absent', sa.Text(), nullable=True),
        
        # Εργασίες
        sa.Column('work_description', sa.Text(), nullable=False),
        sa.Column('work_completed', sa.Text(), nullable=True),
        sa.Column('work_in_progress', sa.Text(), nullable=True),
        
        # Πρόοδος
        sa.Column('progress_percentage', sa.Float(), default=0.0),
        sa.Column('progress_notes', sa.Text(), nullable=True),
        
        # Summaries
        sa.Column('materials_used_summary', sa.Text(), nullable=True),
        sa.Column('equipment_used', sa.Text(), nullable=True),
        sa.Column('issues_summary', sa.Text(), nullable=True),
        
        # Παρατηρήσεις
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('safety_notes', sa.Text(), nullable=True),
        
        # Metadata
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
    )
    op.create_index('ix_daily_reports_project_date', 'daily_reports', ['project_id', 'report_date'], unique=True)
    
    # Issues table
    op.create_table(
        'issues',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('daily_report_id', sa.Integer(), sa.ForeignKey('daily_reports.id'), nullable=True),
        
        # Βασικά στοιχεία
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        
        # Κατηγοριοποίηση
        sa.Column('category', sa.Enum('DELAY', 'QUALITY', 'SAFETY', 'MATERIAL', 'EQUIPMENT', 'WEATHER', 'LABOR', 'OTHER', name='issuecategory'), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='issueseverity'), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', name='issuestatus'), default='OPEN'),
        
        # Χρονοδιάγραμμα
        sa.Column('reported_date', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('resolved_date', sa.DateTime(), nullable=True),
        
        # Επίλυση
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolution_cost', sa.Float(), nullable=True),
        
        # Impact
        sa.Column('delay_days', sa.Integer(), default=0),
        
        # Assignment
        sa.Column('assigned_to', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reported_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
    )
    op.create_index('ix_issues_project_status', 'issues', ['project_id', 'status'])
    op.create_index('ix_issues_severity', 'issues', ['severity'])
    
    # Work Items table
    op.create_table(
        'work_items',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        
        # Εργασία
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        
        # Χρονοδιάγραμμα
        sa.Column('planned_start_date', sa.Date(), nullable=True),
        sa.Column('planned_end_date', sa.Date(), nullable=True),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('actual_end_date', sa.Date(), nullable=True),
        
        # Πρόοδος
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('completion_percentage', sa.Float(), default=0.0),
        
        # Assignment
        sa.Column('assigned_to', sa.Text(), nullable=True),
        
        # Dependencies
        sa.Column('depends_on', sa.Text(), nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
    )
    op.create_index('ix_work_items_project_status', 'work_items', ['project_id', 'status'])
    
    # Labor Logs table
    op.create_table(
        'labor_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('daily_report_id', sa.Integer(), sa.ForeignKey('daily_reports.id'), nullable=True),
        
        # Εργάτης
        sa.Column('worker_name', sa.String(100), nullable=False),
        sa.Column('worker_role', sa.String(100), nullable=True),
        
        # Χρόνος
        sa.Column('work_date', sa.Date(), nullable=False, index=True),
        sa.Column('hours_worked', sa.Float(), default=8.0),
        sa.Column('overtime_hours', sa.Float(), default=0.0),
        
        # Κόστος
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        
        # Σημειώσεις
        sa.Column('tasks_performed', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_labor_logs_project_date', 'labor_logs', ['project_id', 'work_date'])
    
    # Equipment Logs table
    op.create_table(
        'equipment_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('daily_report_id', sa.Integer(), sa.ForeignKey('daily_reports.id'), nullable=True),
        
        # Εξοπλισμός
        sa.Column('equipment_name', sa.String(100), nullable=False),
        sa.Column('equipment_type', sa.String(100), nullable=True),
        
        # Χρήση
        sa.Column('usage_date', sa.Date(), nullable=False, index=True),
        sa.Column('hours_used', sa.Float(), default=0.0),
        
        # Κόστος
        sa.Column('rental_cost', sa.Float(), nullable=True),
        sa.Column('fuel_cost', sa.Float(), nullable=True),
        sa.Column('maintenance_cost', sa.Float(), nullable=True),
        
        # Σημειώσεις
        sa.Column('operator_name', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_equipment_logs_project_date', 'equipment_logs', ['project_id', 'usage_date'])
    
    # Report Photos table
    op.create_table(
        'report_photos',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('daily_report_id', sa.Integer(), sa.ForeignKey('daily_reports.id'), nullable=False),
        
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('thumbnail_path', sa.String(500), nullable=True),
        
        # Metadata
        sa.Column('taken_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )
    
    # Issue Photos table
    op.create_table(
        'issue_photos',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('issue_id', sa.Integer(), sa.ForeignKey('issues.id'), nullable=False),
        
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('thumbnail_path', sa.String(500), nullable=True),
        
        # Metadata
        sa.Column('taken_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('issue_photos')
    op.drop_table('report_photos')
    op.drop_table('equipment_logs')
    op.drop_table('labor_logs')
    op.drop_table('work_items')
    op.drop_table('issues')
    op.drop_table('daily_reports')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS weathercondition")
    op.execute("DROP TYPE IF EXISTS issuecategory")
    op.execute("DROP TYPE IF EXISTS issueseverity")
    op.execute("DROP TYPE IF EXISTS issuestatus")
