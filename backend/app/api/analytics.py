"""
Analytics API Endpoints for ErgoLab Business Intelligence

Provides dashboard stats, project costs, material trends,
budget management, and alerts.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case
from datetime import datetime, timedelta, date
from typing import List, Optional

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.project import Project, ProjectStatus
from app.models.material import Material
from app.models.warehouse import Warehouse
from app.models.inventory import StockTransaction, InventoryStock
from app.models.transfer import Transfer
from app.models.analytics import CostTracking, Budget, Alert
from app.schemas.analytics import (
    ProjectCostSummary,
    MaterialConsumptionTrend,
    ProjectProfitability,
    DashboardStats,
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    WarehouseAnalytics,
    AlertResponse,
    AlertStats,
    SpendingTrend,
    TrendDataPoint,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ==================== DASHBOARD STATISTICS ====================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get comprehensive dashboard statistics for management overview"""
    
    # Project counts
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(
        Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNING])
    ).count()
    completed_projects = db.query(Project).filter(
        Project.status == ProjectStatus.COMPLETED
    ).count()
    
    # Material counts
    total_materials = db.query(Material).count()
    
    # Low stock & out of stock
    low_stock = db.query(InventoryStock).join(Material).filter(
        and_(
            InventoryStock.quantity <= Material.min_stock_level,
            InventoryStock.quantity > 0
        )
    ).count()
    
    out_of_stock = db.query(InventoryStock).filter(
        InventoryStock.quantity == 0
    ).count()
    
    # Warehouse count
    total_warehouses = db.query(Warehouse).count()
    
    # Pending transfers
    pending_transfers = db.query(Transfer).filter(Transfer.status == 'pending').count()
    
    # Budget & spending
    total_budget_result = db.query(func.sum(Budget.total_budget)).scalar()
    total_budget = float(total_budget_result) if total_budget_result else 0.0
    
    # Calculate total spent from stock transactions
    total_spent_result = db.query(
        func.sum(StockTransaction.quantity * Material.unit_price)
    ).join(
        Material, StockTransaction.material_id == Material.id
    ).filter(
        StockTransaction.transaction_type == 'consumption'
    ).scalar()
    total_spent = float(total_spent_result) if total_spent_result else 0.0
    
    budget_remaining = total_budget - total_spent
    budget_utilization = (total_spent / total_budget * 100) if total_budget > 0 else 0
    
    # Top consuming materials (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    top_materials = (
        db.query(
            Material.id,
            Material.name,
            Material.sku,
            Material.unit,
            func.sum(StockTransaction.quantity).label('total_qty'),
            func.sum(StockTransaction.quantity * Material.unit_price).label('total_cost')
        )
        .join(StockTransaction, Material.id == StockTransaction.material_id)
        .filter(
            StockTransaction.transaction_type == 'consumption',
            StockTransaction.created_at >= thirty_days_ago
        )
        .group_by(Material.id, Material.name, Material.sku, Material.unit)
        .order_by(desc('total_qty'))
        .limit(5)
        .all()
    )
    
    # Recent transactions (last 10)
    recent = (
        db.query(
            StockTransaction.id,
            StockTransaction.transaction_type,
            StockTransaction.quantity,
            StockTransaction.created_at.label('created_at'),
            Material.name.label('material_name'),
            Warehouse.name.label('warehouse_name')
        )
        .join(Material, StockTransaction.material_id == Material.id)
        .join(Warehouse, StockTransaction.warehouse_id == Warehouse.id)
        .order_by(StockTransaction.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Spending by project
    spending_by_project = (
        db.query(
            Project.id,
            Project.name,
            Project.code,
            func.coalesce(func.sum(StockTransaction.quantity * Material.unit_price), 0).label('spent')
        )
        .outerjoin(Warehouse, Project.id == Warehouse.project_id)
        .outerjoin(StockTransaction, Warehouse.id == StockTransaction.warehouse_id)
        .outerjoin(Material, StockTransaction.material_id == Material.id)
        .filter(
            StockTransaction.transaction_type == 'consumption'
        )
        .group_by(Project.id, Project.name, Project.code)
        .order_by(desc('spent'))
        .limit(5)
        .all()
    )
    
    # Active alerts
    active_alerts = db.query(Alert).filter(Alert.is_resolved == 0).count()
    critical_alerts = db.query(Alert).filter(
        and_(Alert.is_resolved == 0, Alert.severity == 'critical')
    ).count()
    
    return DashboardStats(
        total_projects=total_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        total_materials=total_materials,
        low_stock_count=low_stock,
        out_of_stock_count=out_of_stock,
        total_warehouses=total_warehouses,
        pending_transfers=pending_transfers,
        total_budget=total_budget,
        total_spent=total_spent,
        budget_remaining=budget_remaining,
        budget_utilization=round(budget_utilization, 2),
        top_consuming_materials=[
            {
                'id': m.id,
                'name': m.name,
                'sku': m.sku,
                'unit': m.unit,
                'quantity': int(m.total_qty),
                'cost': float(m.total_cost) if m.total_cost else 0
            }
            for m in top_materials
        ],
        recent_transactions=[
            {
                'id': t.id,
                'type': t.transaction_type.value if hasattr(t.transaction_type, 'value') else str(t.transaction_type),
                'quantity': t.quantity,
                'date': t.created_at.isoformat() if t.created_at else None,
                'material': t.material_name,
                'warehouse': t.warehouse_name
            }
            for t in recent
        ],
        spending_by_project=[
            {
                'id': p.id,
                'name': p.name,
                'code': p.code,
                'spent': float(p.spent) if p.spent else 0
            }
            for p in spending_by_project
        ],
        active_alerts=active_alerts,
        critical_alerts=critical_alerts
    )


# ==================== PROJECT COST ANALYSIS ====================

@router.get("/projects/costs", response_model=List[ProjectCostSummary])
async def get_all_projects_costs(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get cost summary for all projects"""
    
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)
    
    projects = query.all()
    summaries = []
    
    for project in projects:
        summary = await _calculate_project_cost_summary(db, project)
        summaries.append(summary)
    
    # Sort by total spent descending
    summaries.sort(key=lambda x: x.total_spent, reverse=True)
    return summaries


@router.get("/projects/{project_id}/costs", response_model=ProjectCostSummary)
async def get_project_costs(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get detailed cost summary for a specific project"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return await _calculate_project_cost_summary(db, project)


@router.get("/projects/{project_id}/profitability", response_model=ProjectProfitability)
async def get_project_profitability(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get profitability analysis for a project"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get budget
    budget = db.query(Budget).filter(Budget.project_id == project_id).first()
    total_budget = float(budget.total_budget) if budget else None
    
    # Calculate costs by category
    warehouse = db.query(Warehouse).filter(Warehouse.project_id == project_id).first()
    
    materials_cost = 0.0
    if warehouse:
        cost_result = (
            db.query(func.sum(StockTransaction.quantity * Material.unit_price))
            .join(Material, StockTransaction.material_id == Material.id)
            .filter(
                StockTransaction.warehouse_id == warehouse.id,
                StockTransaction.transaction_type == 'consumption'
            )
            .scalar()
        )
        materials_cost = float(cost_result) if cost_result else 0.0
    
    total_cost = materials_cost
    
    # Calculate profit margin & ROI
    profit_margin = None
    roi = None
    if total_budget and total_budget > 0:
        profit = total_budget - total_cost
        profit_margin = (profit / total_budget) * 100
        roi = (profit / total_cost * 100) if total_cost > 0 else None
    
    # Calculate days active
    days_active = 0
    if project.start_date:
        end_date = project.end_date or datetime.utcnow()
        if hasattr(end_date, 'date'):
            end_date = end_date.date() if hasattr(end_date, 'date') else end_date
        if hasattr(project.start_date, 'date'):
            start_date = project.start_date.date() if hasattr(project.start_date, 'date') else project.start_date
        else:
            start_date = project.start_date
        days_active = (end_date - start_date).days + 1
    
    return ProjectProfitability(
        project_id=project.id,
        project_name=project.name,
        project_code=project.code,
        total_budget=total_budget,
        total_cost=total_cost,
        profit_margin=round(profit_margin, 2) if profit_margin else None,
        roi=round(roi, 2) if roi else None,
        status=project.status.value if hasattr(project.status, 'value') else str(project.status),
        days_active=days_active,
        cost_breakdown={
            'materials': materials_cost,
            'labor': float(budget.labor_budget) if budget else 0,
            'other': float(budget.other_budget) if budget else 0
        }
    )


async def _calculate_project_cost_summary(db: Session, project: Project) -> ProjectCostSummary:
    """Helper to calculate cost summary for a project"""
    
    # Get budget
    budget = db.query(Budget).filter(Budget.project_id == project.id).first()
    total_budget = float(budget.total_budget) if budget else (
        float(project.budget) if project.budget else None
    )
    
    # Get warehouse for this project
    warehouse = db.query(Warehouse).filter(Warehouse.project_id == project.id).first()
    
    # Calculate total spent
    total_spent = 0.0
    if warehouse:
        spent_result = (
            db.query(func.sum(StockTransaction.quantity * Material.unit_price))
            .join(Material, StockTransaction.material_id == Material.id)
            .filter(
                StockTransaction.warehouse_id == warehouse.id,
                StockTransaction.transaction_type == 'consumption'
            )
            .scalar()
        )
        total_spent = float(spent_result) if spent_result else 0.0
    
    # Budget calculations
    budget_remaining = (total_budget - total_spent) if total_budget else None
    budget_utilization = (total_spent / total_budget * 100) if total_budget and total_budget > 0 else None
    
    # Days active & cost per day
    days_active = 0
    cost_per_day = None
    if project.start_date:
        end_date = project.end_date or datetime.utcnow()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()
        if hasattr(project.start_date, 'date'):
            start_date = project.start_date.date()
        else:
            start_date = project.start_date
        days_active = max((end_date - start_date).days + 1, 1)
        cost_per_day = total_spent / days_active
    
    return ProjectCostSummary(
        project_id=project.id,
        project_name=project.name,
        project_code=project.code,
        status=project.status.value if hasattr(project.status, 'value') else str(project.status),
        total_budget=total_budget,
        total_spent=total_spent,
        materials_cost=total_spent,
        budget_remaining=round(budget_remaining, 2) if budget_remaining else None,
        budget_utilization=round(budget_utilization, 2) if budget_utilization else None,
        cost_per_day=round(cost_per_day, 2) if cost_per_day else None,
        days_active=days_active
    )


# ==================== MATERIAL CONSUMPTION TRENDS ====================

@router.get("/materials/trends", response_model=List[MaterialConsumptionTrend])
async def get_material_consumption_trends(
    period_days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(20, ge=1, le=100, description="Max materials to return"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get material consumption trends for the specified period"""
    
    period_start = datetime.utcnow().date() - timedelta(days=period_days)
    period_end = datetime.utcnow().date()
    
    # Get consumption data grouped by material
    consumption = (
        db.query(
            Material.id,
            Material.name,
            Material.sku,
            Material.unit,
            func.sum(StockTransaction.quantity).label('total_qty'),
            func.sum(StockTransaction.quantity * Material.unit_price).label('total_cost')
        )
        .join(StockTransaction, Material.id == StockTransaction.material_id)
        .filter(
            StockTransaction.transaction_type == 'consumption',
            StockTransaction.created_at >= period_start
        )
        .group_by(Material.id, Material.name, Material.sku, Material.unit)
        .order_by(desc('total_qty'))
        .limit(limit)
        .all()
    )
    
    trends = []
    for c in consumption:
        # Get projects where this material was used
        projects = (
            db.query(Project.name)
            .join(Warehouse, Project.id == Warehouse.project_id)
            .join(StockTransaction, Warehouse.id == StockTransaction.warehouse_id)
            .filter(
                StockTransaction.material_id == c.id,
                StockTransaction.transaction_type == 'consumption',
                StockTransaction.created_at >= period_start
            )
            .distinct()
            .all()
        )
        
        avg_daily = float(c.total_qty) / period_days if period_days > 0 else 0
        
        trends.append(MaterialConsumptionTrend(
            material_id=c.id,
            material_name=c.name,
            material_sku=c.sku,
            unit=c.unit or 'pcs',
            period_start=period_start,
            period_end=period_end,
            total_quantity=int(c.total_qty),
            total_cost=round(float(c.total_cost), 2) if c.total_cost else 0.0,
            avg_daily_usage=round(avg_daily, 2),
            projects=[p.name for p in projects]
        ))
    
    return trends


@router.get("/materials/{material_id}/history")
async def get_material_usage_history(
    material_id: int,
    period_days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get detailed usage history for a specific material"""
    
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    period_start = datetime.utcnow() - timedelta(days=period_days)
    
    # Get daily consumption
    daily_usage = (
        db.query(
            func.date(StockTransaction.created_at).label('date'),
            func.sum(StockTransaction.quantity).label('quantity')
        )
        .filter(
            StockTransaction.material_id == material_id,
            StockTransaction.transaction_type == 'consumption',
            StockTransaction.created_at >= period_start
        )
        .group_by(func.date(StockTransaction.created_at))
        .order_by('date')
        .all()
    )
    
    return {
        'material': {
            'id': material.id,
            'name': material.name,
            'sku': material.sku,
            'unit': material.unit
        },
        'period_days': period_days,
        'daily_usage': [
            {'date': str(d.date), 'quantity': int(d.quantity)}
            for d in daily_usage
        ],
        'total_consumed': sum(d.quantity for d in daily_usage),
        'avg_daily': round(sum(d.quantity for d in daily_usage) / period_days, 2) if daily_usage else 0
    }


# ==================== WAREHOUSE ANALYTICS ====================

@router.get("/warehouses/overview", response_model=List[WarehouseAnalytics])
async def get_warehouses_analytics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get analytics overview for all warehouses"""
    
    warehouses = db.query(Warehouse).all()
    analytics = []
    
    for warehouse in warehouses:
        # Total items and value
        inventory_stats = (
            db.query(
                func.count(InventoryStock.id).label('total_items'),
                func.sum(InventoryStock.quantity * Material.unit_price).label('total_value')
            )
            .join(Material, InventoryStock.material_id == Material.id)
            .filter(InventoryStock.warehouse_id == warehouse.id)
            .first()
        )
        
        # Low stock items
        low_stock = (
            db.query(InventoryStock)
            .join(Material)
            .filter(
                InventoryStock.warehouse_id == warehouse.id,
                InventoryStock.quantity <= Material.min_stock_level,
                InventoryStock.quantity > 0
            )
            .count()
        )
        
        # Out of stock
        out_of_stock = (
            db.query(InventoryStock)
            .filter(
                InventoryStock.warehouse_id == warehouse.id,
                InventoryStock.quantity == 0
            )
            .count()
        )
        
        # Top materials by value
        top_materials = (
            db.query(
                Material.name,
                Material.sku,
                InventoryStock.quantity,
                (InventoryStock.quantity * Material.unit_price).label('value')
            )
            .join(Material, InventoryStock.material_id == Material.id)
            .filter(InventoryStock.warehouse_id == warehouse.id)
            .order_by(desc('value'))
            .limit(5)
            .all()
        )
        
        analytics.append(WarehouseAnalytics(
            warehouse_id=warehouse.id,
            warehouse_name=warehouse.name,
            warehouse_code=warehouse.code,
            total_items=inventory_stats.total_items or 0,
            total_value=float(inventory_stats.total_value) if inventory_stats.total_value else 0,
            low_stock_items=low_stock,
            out_of_stock_items=out_of_stock,
            top_materials=[
                {
                    'name': m.name,
                    'sku': m.sku,
                    'quantity': m.quantity,
                    'value': float(m.value) if m.value else 0
                }
                for m in top_materials
            ]
        ))
    
    return analytics


# ==================== BUDGET MANAGEMENT ====================

@router.post("/budgets", response_model=BudgetResponse)
async def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a budget for a project"""
    
    # Check if project exists
    project = db.query(Project).filter(Project.id == budget.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if budget already exists
    existing = db.query(Budget).filter(Budget.project_id == budget.project_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Budget already exists for this project. Use PUT to update.")
    
    db_budget = Budget(**budget.model_dump())
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    
    return db_budget


@router.get("/budgets/{project_id}", response_model=BudgetResponse)
async def get_budget(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get budget for a project"""
    
    budget = db.query(Budget).filter(Budget.project_id == project_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found for this project")
    
    return budget


@router.put("/budgets/{project_id}", response_model=BudgetResponse)
async def update_budget(
    project_id: int,
    budget_update: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update project budget"""
    
    db_budget = db.query(Budget).filter(Budget.project_id == project_id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    update_data = budget_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_budget, key, value)
    
    db.commit()
    db.refresh(db_budget)
    
    return db_budget


# ==================== ALERTS ====================

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    unread_only: bool = False,
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get system alerts"""
    
    query = db.query(Alert).filter(Alert.is_resolved == 0)
    
    if unread_only:
        query = query.filter(Alert.is_read == 0)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    alerts = query.order_by(
        case((Alert.severity == 'critical', 1), (Alert.severity == 'warning', 2), else_=3),
        Alert.created_at.desc()
    ).limit(limit).all()
    
    return alerts


@router.get("/alerts/stats", response_model=AlertStats)
async def get_alert_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get alert statistics"""
    
    total = db.query(Alert).filter(Alert.is_resolved == 0).count()
    unread = db.query(Alert).filter(and_(Alert.is_resolved == 0, Alert.is_read == 0)).count()
    critical = db.query(Alert).filter(and_(Alert.is_resolved == 0, Alert.severity == 'critical')).count()
    warnings = db.query(Alert).filter(and_(Alert.is_resolved == 0, Alert.severity == 'warning')).count()
    info = db.query(Alert).filter(and_(Alert.is_resolved == 0, Alert.severity == 'info')).count()
    
    return AlertStats(
        total=total,
        unread=unread,
        critical=critical,
        warnings=warnings,
        info=info
    )


@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Mark alert as read"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = 1
    db.commit()
    
    return {"message": "Alert marked as read"}


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Resolve an alert"""
    
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_resolved = 1
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = current_user.id
    db.commit()
    
    return {"message": "Alert resolved"}


# ==================== SPENDING TRENDS ====================

@router.get("/spending/trends")
async def get_spending_trends(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get spending trends over time"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    if period == "daily":
        date_trunc = func.date(StockTransaction.created_at)
    elif period == "weekly":
        date_trunc = func.date(StockTransaction.created_at)  # Simplified
    else:  # monthly
        date_trunc = func.date(StockTransaction.created_at)
    
    spending = (
        db.query(
            date_trunc.label('date'),
            func.sum(StockTransaction.quantity * Material.unit_price).label('amount')
        )
        .join(Material, StockTransaction.material_id == Material.id)
        .filter(
            StockTransaction.transaction_type == 'consumption',
            StockTransaction.created_at >= start_date
        )
        .group_by(date_trunc)
        .order_by(date_trunc)
        .all()
    )
    
    data_points = [
        {'date': str(s.date), 'amount': float(s.amount) if s.amount else 0}
        for s in spending
    ]
    
    total = sum(d['amount'] for d in data_points)
    average = total / len(data_points) if data_points else 0
    
    return {
        'period': period,
        'days': days,
        'data_points': data_points,
        'total': round(total, 2),
        'average': round(average, 2)
    }


# ==================== LOW STOCK ALERTS GENERATOR ====================

@router.post("/alerts/generate-low-stock")
async def generate_low_stock_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate alerts for low stock items"""
    
    # Find low stock items
    low_stock_items = (
        db.query(InventoryStock, Material, Warehouse)
        .join(Material, InventoryStock.material_id == Material.id)
        .join(Warehouse, InventoryStock.warehouse_id == Warehouse.id)
        .filter(InventoryStock.quantity <= Material.min_stock_level)
        .all()
    )
    
    alerts_created = 0
    
    for stock, material, warehouse in low_stock_items:
        # Check if alert already exists
        existing = db.query(Alert).filter(
            and_(
                Alert.entity_type == 'material',
                Alert.entity_id == material.id,
                Alert.alert_type == 'low_stock',
                Alert.is_resolved == 0
            )
        ).first()
        
        if not existing:
            severity = 'critical' if stock.quantity == 0 else 'warning'
            title = f"{'Out of Stock' if stock.quantity == 0 else 'Low Stock'}: {material.name}"
            message = f"{material.name} (SKU: {material.sku}) has {stock.quantity} {material.unit} remaining in {warehouse.name}. Minimum level: {material.min_stock_level}"
            
            alert = Alert(
                alert_type='low_stock',
                severity=severity,
                title=title,
                message=message,
                entity_type='material',
                entity_id=material.id
            )
            db.add(alert)
            alerts_created += 1
    
    db.commit()
    
    return {
        "message": f"Generated {alerts_created} new low stock alerts",
        "total_low_stock_items": len(low_stock_items)
    }
