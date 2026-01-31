from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.project import Project
from app.models.material import Material
from app.models.warehouse import Warehouse
from app.models.inventory import StockTransaction
from app.models.reports import (
    DailyReport, Issue, WorkItem, LaborLog, EquipmentLog,
    ReportPhoto, IssuePhoto
)
from app.schemas.reports import (
    DailyReportCreate, DailyReportResponse,
    IssueCreate, IssueUpdate, IssueResponse,
    WorkItemCreate, WorkItemUpdate, WorkItemResponse,
    LaborLogCreate, LaborLogResponse,
    EquipmentLogCreate, EquipmentLogResponse,
    WeeklySummary, MonthlySummary, FinalProjectReport
)
from datetime import datetime, timedelta, date
from typing import List, Optional
import calendar

router = APIRouter()

# ==================== DAILY REPORTS ====================

@router.post("/daily", response_model=DailyReportResponse)
async def create_daily_report(
    report: DailyReportCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Δημιουργία Ημερήσιας Αναφοράς"""
    
    # Check if report already exists for this date
    existing = db.query(DailyReport).filter(
        DailyReport.project_id == report.project_id,
        DailyReport.report_date == report.report_date
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Υπάρχει ήδη αναφορά για την ημερομηνία {report.report_date}"
        )
    
    db_report = DailyReport(
        **report.dict(),
        created_by=current_user.id
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # Add project name
    project = db.query(Project).filter(Project.id == db_report.project_id).first()
    response = DailyReportResponse.model_validate(db_report)
    response.project_name = project.name if project else None
    
    return response

@router.get("/daily", response_model=List[DailyReportResponse])
async def get_daily_reports(
    project_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Λήψη Ημερήσιων Αναφορών"""
    
    query = db.query(DailyReport)
    
    if project_id:
        query = query.filter(DailyReport.project_id == project_id)
    
    if start_date:
        query = query.filter(DailyReport.report_date >= start_date)
    
    if end_date:
        query = query.filter(DailyReport.report_date <= end_date)
    
    reports = query.order_by(DailyReport.report_date.desc()).all()
    
    # Add project names
    results = []
    for report in reports:
        project = db.query(Project).filter(Project.id == report.project_id).first()
        response = DailyReportResponse.model_validate(report)
        response.project_name = project.name if project else None
        results.append(response)
    
    return results

@router.get("/daily/{report_id}", response_model=DailyReportResponse)
async def get_daily_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Λήψη Μεμονωμένης Ημερήσιας Αναφοράς"""
    
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε αναφορά")
    
    project = db.query(Project).filter(Project.id == report.project_id).first()
    response = DailyReportResponse.model_validate(report)
    response.project_name = project.name if project else None
    
    return response

@router.put("/daily/{report_id}", response_model=DailyReportResponse)
async def update_daily_report(
    report_id: int,
    report: DailyReportCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Ενημέρωση Ημερήσιας Αναφοράς"""
    
    db_report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε αναφορά")
    
    for key, value in report.dict(exclude={'project_id'}).items():
        setattr(db_report, key, value)
    
    db.commit()
    db.refresh(db_report)
    
    project = db.query(Project).filter(Project.id == db_report.project_id).first()
    response = DailyReportResponse.model_validate(db_report)
    response.project_name = project.name if project else None
    
    return response

@router.delete("/daily/{report_id}")
async def delete_daily_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Διαγραφή Ημερήσιας Αναφοράς"""
    
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε αναφορά")
    
    db.delete(report)
    db.commit()
    
    return {"message": "Η αναφορά διαγράφηκε επιτυχώς"}

# ==================== ISSUES ====================

@router.post("/issues", response_model=IssueResponse)
async def create_issue(
    issue: IssueCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Δημιουργία Προβλήματος"""
    
    db_issue = Issue(
        **issue.dict(),
        reported_by=current_user.id
    )
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    
    project = db.query(Project).filter(Project.id == db_issue.project_id).first()
    response = IssueResponse.model_validate(db_issue)
    response.project_name = project.name if project else None
    
    return response

@router.get("/issues", response_model=List[IssueResponse])
async def get_issues(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Λήψη Προβλημάτων"""
    
    query = db.query(Issue)
    
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    
    if status:
        query = query.filter(Issue.status == status)
    
    if severity:
        query = query.filter(Issue.severity == severity)
    
    if category:
        query = query.filter(Issue.category == category)
    
    issues = query.order_by(Issue.reported_date.desc()).all()
    
    results = []
    for issue in issues:
        project = db.query(Project).filter(Project.id == issue.project_id).first()
        response = IssueResponse.model_validate(issue)
        response.project_name = project.name if project else None
        results.append(response)
    
    return results

@router.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Λήψη Μεμονωμένου Προβλήματος"""
    
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε πρόβλημα")
    
    project = db.query(Project).filter(Project.id == issue.project_id).first()
    response = IssueResponse.model_validate(issue)
    response.project_name = project.name if project else None
    
    return response

@router.put("/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    issue_update: IssueUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Ενημέρωση Προβλήματος"""
    
    db_issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not db_issue:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε πρόβλημα")
    
    update_data = issue_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_issue, key, value)
    
    db.commit()
    db.refresh(db_issue)
    
    project = db.query(Project).filter(Project.id == db_issue.project_id).first()
    response = IssueResponse.model_validate(db_issue)
    response.project_name = project.name if project else None
    
    return response

@router.delete("/issues/{issue_id}")
async def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Διαγραφή Προβλήματος"""
    
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε πρόβλημα")
    
    db.delete(issue)
    db.commit()
    
    return {"message": "Το πρόβλημα διαγράφηκε επιτυχώς"}

# ==================== WORK ITEMS ====================

@router.post("/work-items", response_model=WorkItemResponse)
async def create_work_item(
    item: WorkItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Δημιουργία Εργασίας"""
    
    db_item = WorkItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item

@router.get("/work-items", response_model=List[WorkItemResponse])
async def get_work_items(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Λήψη Εργασιών"""
    
    query = db.query(WorkItem)
    
    if project_id:
        query = query.filter(WorkItem.project_id == project_id)
    
    if status:
        query = query.filter(WorkItem.status == status)
    
    return query.order_by(WorkItem.planned_start_date).all()

@router.put("/work-items/{item_id}", response_model=WorkItemResponse)
async def update_work_item(
    item_id: int,
    item_update: WorkItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Ενημέρωση Εργασίας"""
    
    db_item = db.query(WorkItem).filter(WorkItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε εργασία")
    
    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    
    return db_item

@router.delete("/work-items/{item_id}")
async def delete_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Διαγραφή Εργασίας"""
    
    db_item = db.query(WorkItem).filter(WorkItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε εργασία")
    
    db.delete(db_item)
    db.commit()
    
    return {"message": "Η εργασία διαγράφηκε επιτυχώς"}

# ==================== LABOR LOGS ====================

@router.post("/labor-logs", response_model=LaborLogResponse)
async def create_labor_log(
    log: LaborLogCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Καταγραφή Εργασίας"""
    
    # Calculate total cost
    total_cost = None
    if log.hourly_rate:
        total_hours = log.hours_worked + log.overtime_hours
        total_cost = log.hourly_rate * total_hours
    
    db_log = LaborLog(
        **log.dict(),
        total_cost=total_cost
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return db_log

@router.get("/labor-logs", response_model=List[LaborLogResponse])
async def get_labor_logs(
    project_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Λήψη Καταγραφών Εργασίας"""
    
    query = db.query(LaborLog)
    
    if project_id:
        query = query.filter(LaborLog.project_id == project_id)
    
    if start_date:
        query = query.filter(LaborLog.work_date >= start_date)
    
    if end_date:
        query = query.filter(LaborLog.work_date <= end_date)
    
    return query.order_by(LaborLog.work_date.desc()).all()

@router.delete("/labor-logs/{log_id}")
async def delete_labor_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Διαγραφή Καταγραφής Εργασίας"""
    
    db_log = db.query(LaborLog).filter(LaborLog.id == log_id).first()
    if not db_log:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε καταγραφή")
    
    db.delete(db_log)
    db.commit()
    
    return {"message": "Η καταγραφή διαγράφηκε επιτυχώς"}

# ==================== EQUIPMENT LOGS ====================

@router.post("/equipment-logs", response_model=EquipmentLogResponse)
async def create_equipment_log(
    log: EquipmentLogCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Καταγραφή Εξοπλισμού"""
    
    db_log = EquipmentLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return db_log

@router.get("/equipment-logs", response_model=List[EquipmentLogResponse])
async def get_equipment_logs(
    project_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Λήψη Καταγραφών Εξοπλισμού"""
    
    query = db.query(EquipmentLog)
    
    if project_id:
        query = query.filter(EquipmentLog.project_id == project_id)
    
    if start_date:
        query = query.filter(EquipmentLog.usage_date >= start_date)
    
    if end_date:
        query = query.filter(EquipmentLog.usage_date <= end_date)
    
    return query.order_by(EquipmentLog.usage_date.desc()).all()

@router.delete("/equipment-logs/{log_id}")
async def delete_equipment_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Διαγραφή Καταγραφής Εξοπλισμού"""
    
    db_log = db.query(EquipmentLog).filter(EquipmentLog.id == log_id).first()
    if not db_log:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε καταγραφή")
    
    db.delete(db_log)
    db.commit()
    
    return {"message": "Η καταγραφή διαγράφηκε επιτυχώς"}

# ==================== WEEKLY SUMMARY ====================

@router.get("/weekly-summary/{project_id}", response_model=WeeklySummary)
async def get_weekly_summary(
    project_id: int,
    week_start: date = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Εβδομαδιαία Σύνοψη"""
    
    week_end = week_start + timedelta(days=6)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε έργο")
    
    # Get daily reports for the week
    daily_reports = db.query(DailyReport).filter(
        DailyReport.project_id == project_id,
        DailyReport.report_date >= week_start,
        DailyReport.report_date <= week_end
    ).order_by(DailyReport.report_date).all()
    
    # Calculate totals
    total_workers = sum(r.workers_count for r in daily_reports)
    
    # Labor logs
    labor_logs = db.query(LaborLog).filter(
        LaborLog.project_id == project_id,
        LaborLog.work_date >= week_start,
        LaborLog.work_date <= week_end
    ).all()
    
    total_hours = sum(l.hours_worked + l.overtime_hours for l in labor_logs)
    total_cost = sum(l.total_cost for l in labor_logs if l.total_cost)
    
    # Get issues
    issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.reported_date >= datetime.combine(week_start, datetime.min.time()),
        Issue.reported_date <= datetime.combine(week_end, datetime.max.time())
    ).all()
    
    issues_count = len(issues)
    critical_issues = len([i for i in issues if str(i.severity) == 'critical' or (hasattr(i.severity, 'value') and i.severity.value == 'critical')])
    
    # Work completed
    work_completed = [r.work_completed for r in daily_reports if r.work_completed]
    
    # Materials used (from daily reports summaries)
    materials_used = []
    for report in daily_reports:
        if report.materials_used_summary:
            materials_used.append({
                'date': report.report_date.isoformat(),
                'summary': report.materials_used_summary
            })
    
    # Progress change
    if daily_reports:
        first_progress = daily_reports[0].progress_percentage
        last_progress = daily_reports[-1].progress_percentage
        progress_change = last_progress - first_progress
    else:
        progress_change = 0.0
    
    return WeeklySummary(
        project_id=project_id,
        project_name=project.name,
        week_start=week_start,
        week_end=week_end,
        total_workers=total_workers,
        total_hours=total_hours,
        total_cost=total_cost,
        work_completed=work_completed,
        issues_count=issues_count,
        critical_issues=critical_issues,
        materials_used=materials_used,
        progress_change=progress_change
    )

# ==================== MONTHLY SUMMARY ====================

@router.get("/monthly-summary/{project_id}", response_model=MonthlySummary)
async def get_monthly_summary(
    project_id: int,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Μηνιαία Σύνοψη"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε έργο")
    
    # Get month range
    _, last_day = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)
    
    # Daily reports
    daily_reports = db.query(DailyReport).filter(
        DailyReport.project_id == project_id,
        DailyReport.report_date >= month_start,
        DailyReport.report_date <= month_end
    ).order_by(DailyReport.report_date.desc()).all()
    
    total_days_worked = len(daily_reports)
    total_workers = sum(r.workers_count for r in daily_reports)
    
    # Labor
    labor_logs = db.query(LaborLog).filter(
        LaborLog.project_id == project_id,
        LaborLog.work_date >= month_start,
        LaborLog.work_date <= month_end
    ).all()
    
    total_labor_hours = sum(l.hours_worked + l.overtime_hours for l in labor_logs)
    total_labor_cost = sum(l.total_cost for l in labor_logs if l.total_cost)
    
    # Equipment
    equipment_logs = db.query(EquipmentLog).filter(
        EquipmentLog.project_id == project_id,
        EquipmentLog.usage_date >= month_start,
        EquipmentLog.usage_date <= month_end
    ).all()
    
    total_equipment_cost = sum(
        (e.rental_cost or 0) + (e.fuel_cost or 0) + (e.maintenance_cost or 0)
        for e in equipment_logs
    )
    
    # Materials cost (from transactions)
    warehouses = db.query(Warehouse).filter(Warehouse.project_id == project_id).all()
    warehouse_ids = [w.id for w in warehouses]
    
    total_materials_cost = 0.0
    if warehouse_ids:
        materials_cost = (
            db.query(func.sum(StockTransaction.quantity * Material.unit_price))
            .join(Material)
            .filter(
                StockTransaction.warehouse_id.in_(warehouse_ids),
                StockTransaction.transaction_type == 'consumption',
                StockTransaction.transaction_date >= datetime.combine(month_start, datetime.min.time()),
                StockTransaction.transaction_date <= datetime.combine(month_end, datetime.max.time())
            )
            .scalar()
        )
        total_materials_cost = float(materials_cost) if materials_cost else 0.0
    
    total_cost = total_labor_cost + total_equipment_cost + total_materials_cost
    
    # Budget
    from app.models.analytics import Budget
    budget = db.query(Budget).filter(Budget.project_id == project_id).first()
    budget_used_percentage = None
    if budget and budget.total_budget > 0:
        budget_used_percentage = (total_cost / float(budget.total_budget)) * 100
    
    # Progress
    latest_report = daily_reports[0] if daily_reports else None
    progress_percentage = latest_report.progress_percentage if latest_report else 0.0
    
    # Issues
    month_start_dt = datetime.combine(month_start, datetime.min.time())
    month_end_dt = datetime.combine(month_end, datetime.max.time())
    
    issues_opened = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.reported_date >= month_start_dt,
        Issue.reported_date <= month_end_dt
    ).count()
    
    issues_resolved = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.resolved_date >= month_start_dt,
        Issue.resolved_date <= month_end_dt
    ).count()
    
    issues_pending = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.in_(['open', 'in_progress'])
    ).count()
    
    # Major milestones (from work items completed this month)
    completed_work = db.query(WorkItem).filter(
        WorkItem.project_id == project_id,
        WorkItem.status == 'completed',
        WorkItem.actual_end_date >= month_start,
        WorkItem.actual_end_date <= month_end
    ).all()
    
    major_milestones = [w.name for w in completed_work]
    
    return MonthlySummary(
        project_id=project_id,
        project_name=project.name,
        month=month,
        year=year,
        total_days_worked=total_days_worked,
        total_workers=total_workers,
        total_labor_hours=total_labor_hours,
        total_labor_cost=total_labor_cost,
        total_materials_cost=total_materials_cost,
        total_equipment_cost=total_equipment_cost,
        total_cost=total_cost,
        budget_used_percentage=budget_used_percentage,
        progress_percentage=progress_percentage,
        issues_opened=issues_opened,
        issues_resolved=issues_resolved,
        issues_pending=issues_pending,
        major_milestones=major_milestones
    )

# ==================== FINAL PROJECT REPORT ====================

@router.get("/final-report/{project_id}", response_model=FinalProjectReport)
async def get_final_project_report(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Τελική Αναφορά Έργου"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε έργο")
    
    # Duration
    if project.start_date:
        end_dt = project.end_date if project.end_date else datetime.now()
        if hasattr(project.start_date, 'date'):
            start_d = project.start_date.date()
        else:
            start_d = project.start_date
        if hasattr(end_dt, 'date'):
            end_d = end_dt.date()
        else:
            end_d = end_dt
        duration_days = (end_d - start_d).days + 1
    else:
        duration_days = 0
    
    # Budget
    from app.models.analytics import Budget
    budget = db.query(Budget).filter(Budget.project_id == project_id).first()
    total_budget = float(budget.total_budget) if budget else None
    
    # Labor cost
    labor_cost = db.query(func.sum(LaborLog.total_cost)).filter(
        LaborLog.project_id == project_id
    ).scalar() or 0.0
    
    # Equipment cost
    equipment_cost_sum = db.query(
        func.sum(
            func.coalesce(EquipmentLog.rental_cost, 0) +
            func.coalesce(EquipmentLog.fuel_cost, 0) +
            func.coalesce(EquipmentLog.maintenance_cost, 0)
        )
    ).filter(EquipmentLog.project_id == project_id).scalar() or 0.0
    
    # Materials cost
    warehouses = db.query(Warehouse).filter(Warehouse.project_id == project_id).all()
    warehouse_ids = [w.id for w in warehouses]
    
    materials_cost = 0.0
    if warehouse_ids:
        mat_cost = (
            db.query(func.sum(StockTransaction.quantity * Material.unit_price))
            .join(Material)
            .filter(
                StockTransaction.warehouse_id.in_(warehouse_ids),
                StockTransaction.transaction_type == 'consumption'
            )
            .scalar()
        )
        materials_cost = float(mat_cost) if mat_cost else 0.0
    
    total_cost = float(labor_cost) + float(equipment_cost_sum) + materials_cost
    
    # Budget variance
    budget_variance = None
    budget_variance_percentage = None
    if total_budget:
        budget_variance = total_budget - total_cost
        budget_variance_percentage = (budget_variance / total_budget) * 100
    
    # Labor stats
    unique_workers = db.query(func.count(func.distinct(LaborLog.worker_name))).filter(
        LaborLog.project_id == project_id
    ).scalar() or 0
    
    total_labor_hours = db.query(
        func.sum(LaborLog.hours_worked + LaborLog.overtime_hours)
    ).filter(LaborLog.project_id == project_id).scalar() or 0.0
    
    # Issues
    total_issues = db.query(Issue).filter(Issue.project_id == project_id).count()
    critical_issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.severity == 'critical'
    ).count()
    issues_resolved = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.in_(['resolved', 'closed'])
    ).count()
    
    # Progress
    latest_report = db.query(DailyReport).filter(
        DailyReport.project_id == project_id
    ).order_by(DailyReport.report_date.desc()).first()
    
    final_progress = latest_report.progress_percentage if latest_report else 0.0
    
    # Completion status (Ελληνικά)
    status_map = {
        'completed': 'Ολοκληρώθηκε',
        'active': 'Σε εξέλιξη',
        'on_hold': 'Σε αναστολή',
        'planning': 'Σχεδιασμός',
        'cancelled': 'Ακυρώθηκε'
    }
    status_value = project.status.value if hasattr(project.status, 'value') else str(project.status)
    completion_status = status_map.get(status_value, status_value)
    
    # Key achievements (completed work items)
    completed_work = db.query(WorkItem).filter(
        WorkItem.project_id == project_id,
        WorkItem.status == 'completed'
    ).all()
    key_achievements = [w.name for w in completed_work[:10]]  # Top 10
    
    # Major challenges (critical/high severity issues)
    major_issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.severity.in_(['critical', 'high'])
    ).all()
    major_challenges = [f"{i.title} ({i.category})" for i in major_issues[:10]]
    
    # Lessons learned (from resolved issues)
    resolved_issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status == 'resolved',
        Issue.resolution_notes.isnot(None)
    ).all()
    lessons_learned = [i.resolution_notes for i in resolved_issues[:5] if i.resolution_notes]
    
    # Convert dates
    start_date = None
    end_date = None
    if project.start_date:
        start_date = project.start_date.date() if hasattr(project.start_date, 'date') else project.start_date
    if project.end_date:
        end_date = project.end_date.date() if hasattr(project.end_date, 'date') else project.end_date
    
    return FinalProjectReport(
        project_id=project.id,
        project_name=project.name,
        project_code=project.code,
        start_date=start_date,
        end_date=end_date,
        duration_days=duration_days,
        total_budget=total_budget,
        total_cost=total_cost,
        budget_variance=budget_variance,
        budget_variance_percentage=budget_variance_percentage,
        materials_cost=materials_cost,
        labor_cost=float(labor_cost),
        equipment_cost=float(equipment_cost_sum),
        other_costs=0.0,
        total_workers_employed=unique_workers,
        total_labor_hours=float(total_labor_hours),
        total_issues=total_issues,
        critical_issues=critical_issues,
        issues_resolved=issues_resolved,
        final_progress=final_progress,
        completion_status=completion_status,
        key_achievements=key_achievements,
        major_challenges=major_challenges,
        lessons_learned=lessons_learned
    )

# ==================== DASHBOARD STATS ====================

@router.get("/dashboard-stats/{project_id}")
async def get_dashboard_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Στατιστικά Dashboard για Έργο"""
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Δεν βρέθηκε έργο")
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # Today's report
    today_report = db.query(DailyReport).filter(
        DailyReport.project_id == project_id,
        DailyReport.report_date == today
    ).first()
    
    # Open issues
    open_issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.in_(['open', 'in_progress'])
    ).count()
    
    critical_open = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.in_(['open', 'in_progress']),
        Issue.severity == 'critical'
    ).count()
    
    # This week's labor hours
    week_hours = db.query(func.sum(LaborLog.hours_worked + LaborLog.overtime_hours)).filter(
        LaborLog.project_id == project_id,
        LaborLog.work_date >= week_start,
        LaborLog.work_date <= today
    ).scalar() or 0
    
    # Work items status
    work_items_total = db.query(WorkItem).filter(WorkItem.project_id == project_id).count()
    work_items_completed = db.query(WorkItem).filter(
        WorkItem.project_id == project_id,
        WorkItem.status == 'completed'
    ).count()
    work_items_in_progress = db.query(WorkItem).filter(
        WorkItem.project_id == project_id,
        WorkItem.status == 'in_progress'
    ).count()
    
    # Latest progress
    latest_report = db.query(DailyReport).filter(
        DailyReport.project_id == project_id
    ).order_by(DailyReport.report_date.desc()).first()
    
    current_progress = latest_report.progress_percentage if latest_report else 0
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "today": {
            "has_report": today_report is not None,
            "workers_count": today_report.workers_count if today_report else 0,
            "weather": today_report.weather_condition.value if today_report and today_report.weather_condition else None
        },
        "issues": {
            "open": open_issues,
            "critical": critical_open
        },
        "this_week": {
            "labor_hours": float(week_hours)
        },
        "work_items": {
            "total": work_items_total,
            "completed": work_items_completed,
            "in_progress": work_items_in_progress,
            "completion_rate": (work_items_completed / work_items_total * 100) if work_items_total > 0 else 0
        },
        "progress": {
            "current": current_progress,
            "last_updated": latest_report.report_date.isoformat() if latest_report else None
        }
    }
