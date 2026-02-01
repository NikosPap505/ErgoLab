from enum import Enum
from typing import List
from functools import wraps

from fastapi import Depends, HTTPException, status

from app.api.auth import get_current_user
from app.models.user import User


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    WORKER = "worker"
    VIEWER = "viewer"


class Permission(str, Enum):
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    MATERIAL_CREATE = "material:create"
    MATERIAL_READ = "material:read"
    MATERIAL_UPDATE = "material:update"
    MATERIAL_DELETE = "material:delete"

    INVENTORY_TRANSACTION = "inventory:transaction"
    INVENTORY_TRANSFER = "inventory:transfer"

    REPORT_CREATE = "report:create"
    REPORT_READ = "report:read"
    REPORT_UPDATE = "report:update"
    REPORT_DELETE = "report:delete"

    ISSUE_CREATE = "issue:create"
    ISSUE_READ = "issue:read"
    ISSUE_UPDATE = "issue:update"
    ISSUE_DELETE = "issue:delete"
    ISSUE_ASSIGN = "issue:assign"

    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"

    BUDGET_VIEW = "budget:view"
    BUDGET_MANAGE = "budget:manage"

    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"

    SETTINGS_VIEW = "settings:view"
    SETTINGS_MANAGE = "settings:manage"


ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],
    Role.MANAGER: [
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.MATERIAL_CREATE,
        Permission.MATERIAL_READ,
        Permission.MATERIAL_UPDATE,
        Permission.MATERIAL_DELETE,
        Permission.INVENTORY_TRANSACTION,
        Permission.INVENTORY_TRANSFER,
        Permission.REPORT_CREATE,
        Permission.REPORT_READ,
        Permission.REPORT_UPDATE,
        Permission.REPORT_DELETE,
        Permission.ISSUE_CREATE,
        Permission.ISSUE_READ,
        Permission.ISSUE_UPDATE,
        Permission.ISSUE_DELETE,
        Permission.ISSUE_ASSIGN,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.BUDGET_VIEW,
        Permission.BUDGET_MANAGE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.SETTINGS_VIEW,
    ],
    Role.SUPERVISOR: [
        Permission.PROJECT_READ,
        Permission.MATERIAL_READ,
        Permission.MATERIAL_UPDATE,
        Permission.INVENTORY_TRANSACTION,
        Permission.INVENTORY_TRANSFER,
        Permission.REPORT_CREATE,
        Permission.REPORT_READ,
        Permission.REPORT_UPDATE,
        Permission.ISSUE_CREATE,
        Permission.ISSUE_READ,
        Permission.ISSUE_UPDATE,
        Permission.ISSUE_ASSIGN,
        Permission.ANALYTICS_VIEW,
        Permission.BUDGET_VIEW,
        Permission.SETTINGS_VIEW,
    ],
    Role.WORKER: [
        Permission.PROJECT_READ,
        Permission.MATERIAL_READ,
        Permission.REPORT_READ,
        Permission.ISSUE_CREATE,
        Permission.ISSUE_READ,
        Permission.SETTINGS_VIEW,
    ],
    Role.VIEWER: [
        Permission.PROJECT_READ,
        Permission.MATERIAL_READ,
        Permission.REPORT_READ,
        Permission.ISSUE_READ,
        Permission.ANALYTICS_VIEW,
        Permission.BUDGET_VIEW,
    ],
}


def _normalize_role(user: User) -> Role | None:
    if not user or not user.role:
        return None
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    try:
        return Role(role_value)
    except ValueError:
        return None


def has_permission(user: User, permission: Permission) -> bool:
    role = _normalize_role(user)
    if not role:
        return False
    if role == Role.ADMIN:
        return True
    return permission in ROLE_PERMISSIONS.get(role, [])


def require_permission(permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(allowed_roles: List[Role]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            role = _normalize_role(current_user)
            if role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_permission(permission: Permission):
    def _check(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )
        return current_user
    return _check


def check_role(allowed_roles: List[Role]):
    def _check(current_user: User = Depends(get_current_user)):
        role = _normalize_role(current_user)
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return _check
