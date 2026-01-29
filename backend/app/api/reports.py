import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.inventory import StockTransaction, TransactionType
from app.models.material import Material
from app.models.report import Report, ReportType

router = APIRouter(prefix="/api/reports", tags=["Reports"])


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
                "quantity": r.total_quantity,
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
