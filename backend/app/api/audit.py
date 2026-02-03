from typing import List, Optional, Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.user import User, UserRole


router = APIRouter(prefix="/api/audit", tags=["Audit"])


SENSITIVE_KEYS = {
    "password", "password_hash", "hashed_password", 
    "token", "access_token", "refresh_token", 
    "secret", "ssn", "email", "dob", "credit_card",
    "api_key"
}


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redact sensitive keys in dictionaries and lists."""
    if isinstance(data, dict):
        return {
            k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else redact_sensitive_data(v)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    return data


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_email_hash: Optional[str]
    action: str
    table_name: str
    record_id: Optional[int]
    old_values: Optional[dict]
    new_values: Optional[dict]
    ip_address: Optional[str]
    timestamp: datetime

    @field_validator("old_values", "new_values")
    @classmethod
    def sanitize_payload(cls, v):
        return redact_sensitive_data(v)

    class Config:
        from_attributes = True


@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    table_name: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get audit logs. Admin/Manager only."""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Build query
    query = db.query(AuditLog)
    
    # Filter by date range
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = query.filter(AuditLog.timestamp >= since)
    
    if table_name:
        query = query.filter(AuditLog.table_name == table_name)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    # Order by most recent first
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Paginate
    logs = query.offset(skip).limit(limit).all()
    
    return logs
