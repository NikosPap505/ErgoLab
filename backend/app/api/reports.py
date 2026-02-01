import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.inventory import StockTransaction, TransactionType
from app.models.material import Material
from app.models.report import Report, ReportType

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/")
def get_reports(
    type: Optional[str] = Query(None, description="Report type: inventory, consumables, transfers"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generic reports endpoint - returns saved reports or generates basic reports.
    
    Supported types:
    - inventory: Current inventory status
    - consumables: Material consumption
    - transfers: Material transfers
    """
    
    # Parse dates if provided with error handling
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid start_date format: '{start_date}'. Expected ISO format (YYYY-MM-DD)."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid end_date format: '{end_date}'. Expected ISO format (YYYY-MM-DD)."
            )
    
    # If no specific type, return list of saved reports
    if not type:
        query = db.query(Report).filter(Report.generated_by_id == current_user.id)
        
        if project_id:
            query = query.filter(Report.project_id == project_id)
        if start_dt:
            query = query.filter(Report.period_start >= start_dt)
        if end_dt:
            query = query.filter(Report.period_end <= end_dt)
        
        reports = query.order_by(Report.created_at.desc()).limit(50).all()
        
        return {
            "reports": [
                {
                    "id": r.id,
                    "title": r.title,
                    "type": r.report_type.value if r.report_type else None,
                    "project_id": r.project_id,
                    "period_start": r.period_start.isoformat() if r.period_start else None,
                    "period_end": r.period_end.isoformat() if r.period_end else None,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "total_cost": float(r.total_cost) if r.total_cost else 0,
                }
                for r in reports
            ]
        }
    
    # Handle specific report types
    if type == "inventory":
        return _generate_inventory_report(db, start_dt, end_dt, project_id)
    elif type == "consumables":
        return _generate_consumables_report(db, start_dt, end_dt, project_id)
    elif type == "transfers":
        return _generate_transfers_report(db, start_dt, end_dt, project_id)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown report type: '{type}'. Available types: inventory, consumables, transfers"
        )


def _generate_inventory_report(db: Session, start_date, end_date, project_id):
    """Generate current inventory status report"""
    from app.models.inventory import InventoryStock
    from app.models.warehouse import Warehouse
    
    query = db.query(
        Material.id,
        Material.name,
        Material.sku,
        Material.category,
        Material.unit,
        Material.min_stock_level,
        Warehouse.id.label('warehouse_id'),
        Warehouse.name.label('warehouse_name'),
        InventoryStock.quantity,
        InventoryStock.last_updated,
    ).join(
        InventoryStock, Material.id == InventoryStock.material_id
    ).join(
        Warehouse, InventoryStock.warehouse_id == Warehouse.id
    )
    
    # Apply date filters on InventoryStock.last_updated
    if start_date:
        query = query.filter(InventoryStock.last_updated >= start_date)
    if end_date:
        query = query.filter(InventoryStock.last_updated <= end_date)
    
    if project_id:
        query = query.filter(Warehouse.project_id == project_id)
    
    results = query.all()
    
    return {
        "type": "inventory",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "project_id": project_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
        "items": [
            {
                "material_id": r.id,
                "material_name": r.name,
                "sku": r.sku,
                "category": r.category,
                "unit": r.unit,
                "warehouse_id": r.warehouse_id,
                "warehouse": r.warehouse_name,
                "quantity": float(r.quantity) if r.quantity else 0,
                "min_stock": float(r.min_stock_level) if r.min_stock_level else 0,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                "status": "low" if (r.quantity and r.min_stock_level and r.quantity < r.min_stock_level) else "ok",
            }
            for r in results
        ],
        "summary": {
            "total_items": len(results),
            "low_stock_items": sum(1 for r in results if r.quantity and r.min_stock_level and r.quantity < r.min_stock_level),
        }
    }


def _generate_consumables_report(db: Session, start_date, end_date, project_id):
    """Generate material consumption report"""
    query = (
        db.query(
            Material.id,
            Material.name,
            Material.sku,
            Material.category,
            Material.unit,
            func.sum(StockTransaction.quantity).label("total_quantity"),
            func.sum(StockTransaction.total_cost).label("total_cost"),
        )
        .join(Material, StockTransaction.material_id == Material.id)
        .filter(StockTransaction.transaction_type == TransactionType.CONSUMPTION)
    )
    
    if start_date:
        query = query.filter(StockTransaction.created_at >= start_date)
    if end_date:
        query = query.filter(StockTransaction.created_at <= end_date)
    
    if project_id:
        from app.models.warehouse import Warehouse
        query = query.join(Warehouse, StockTransaction.warehouse_id == Warehouse.id).filter(
            Warehouse.project_id == project_id
        )
    
    results = query.group_by(Material.id, Material.name, Material.sku, Material.category, Material.unit).all()
    
    total_cost = sum(float(r.total_cost) if r.total_cost else 0 for r in results)
    
    return {
        "type": "consumables",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "project_id": project_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
        "items": [
            {
                "material_id": r.id,
                "material_name": r.name,
                "sku": r.sku,
                "category": r.category,
                "unit": r.unit,
                "quantity": float(r.total_quantity) if r.total_quantity else 0,
                "total_cost": float(r.total_cost) if r.total_cost else 0,
            }
            for r in results
        ],
        "summary": {
            "total_items": len(results),
            "total_cost": total_cost,
        }
    }


def _generate_transfers_report(db: Session, start_date, end_date, project_id):
    """Generate material transfers report"""
    from app.models.transfer import Transfer
    from app.models.warehouse import Warehouse
    
    query = db.query(Transfer).join(
        Warehouse, Transfer.from_warehouse_id == Warehouse.id
    )
    
    if start_date:
        query = query.filter(Transfer.created_at >= start_date)
    if end_date:
        query = query.filter(Transfer.created_at <= end_date)
    
    if project_id:
        query = query.filter(Warehouse.project_id == project_id)
    
    # Get total count before applying limit
    total_count = query.count()
    
    # Apply limit to prevent unbounded result sets
    limit = 50
    transfers = query.order_by(Transfer.created_at.desc()).limit(limit).all()
    
    return {
        "type": "transfers",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "project_id": project_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
        "items": [
            {
                "id": t.id,
                "transfer_number": t.transfer_number,
                "from_warehouse_id": t.from_warehouse_id,
                "to_warehouse_id": t.to_warehouse_id,
                "status": t.status.value if t.status else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "notes": t.notes,
            }
            for t in transfers
        ],
        "summary": {
            "total_transfers": total_count,
            "returned_count": len(transfers),
            "truncated": total_count > limit,
            "limit": limit,
        }
    }


@router.get("/consumables/project/{project_id}")
def generate_consumables_by_project_report(
    project_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.warehouse import Warehouse

    warehouse = db.query(Warehouse).filter(Warehouse.project_id == project_id).first()
    if not warehouse:
        return {"error": "No warehouse found for this project"}

    query = (
        db.query(
            Material.name,
            Material.sku,
            Material.category,
            func.sum(StockTransaction.quantity).label("total_quantity"),
            func.sum(StockTransaction.total_cost).label("total_cost"),
        )
        .join(Material, StockTransaction.material_id == Material.id)
        .filter(
            StockTransaction.warehouse_id == warehouse.id,
            StockTransaction.transaction_type == TransactionType.CONSUMPTION,
        )
    )

    if start_date:
        query = query.filter(StockTransaction.created_at >= start_date)
    if end_date:
        query = query.filter(StockTransaction.created_at <= end_date)

    results = query.group_by(Material.id, Material.name, Material.sku, Material.category).all()

    grand_total = sum(r.total_cost or 0 for r in results)

    report_data = {
        "items": [
            {
                "material_name": r.name,
                "sku": r.sku,
                "category": r.category,
                "quantity": float(r.total_quantity) if r.total_quantity else 0,
                "total_cost": float(r.total_cost) if r.total_cost else 0,
            }
            for r in results
        ],
        "grand_total": float(grand_total),
    }

    report = Report(
        project_id=project_id,
        report_type=ReportType.CONSUMABLES_BY_PROJECT,
        title=f"Consumables Report - Project {project_id}",
        period_start=start_date,
        period_end=end_date,
        total_cost=grand_total,
        report_data=json.dumps(report_data),
        generated_by_id=current_user.id,
    )
    db.add(report)
    db.commit()

    return report_data


@router.get("/consumables/total")
def generate_total_consumables_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = (
        db.query(
            Material.category,
            func.sum(StockTransaction.quantity).label("total_quantity"),
            func.sum(StockTransaction.total_cost).label("total_cost"),
        )
        .join(Material, StockTransaction.material_id == Material.id)
        .filter(StockTransaction.transaction_type == TransactionType.CONSUMPTION)
    )

    if start_date:
        query = query.filter(StockTransaction.created_at >= start_date)
    if end_date:
        query = query.filter(StockTransaction.created_at <= end_date)

    results = query.group_by(Material.category).all()

    grand_total = sum(r.total_cost or 0 for r in results)

    return {
        "by_category": [
            {
                "category": r.category,
                "total_quantity": r.total_quantity,
                "total_cost": float(r.total_cost) if r.total_cost else 0,
            }
            for r in results
        ],
        "grand_total": float(grand_total),
    }
