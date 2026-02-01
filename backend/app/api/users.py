from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import Permission, ROLE_PERMISSIONS, Role, check_permission
from app.api.auth import get_current_user
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import (
    ChangeRoleRequest,
    UserCreate,
    UserPermissions,
    UserResponse,
    UserRole,
    UserUpdate,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.USER_READ)),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/permissions", response_model=UserPermissions)
async def get_my_permissions(current_user: User = Depends(get_current_user)):
    role_value = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    role = Role(role_value) if role_value in Role._value2member_map_ else None
    permissions = ROLE_PERMISSIONS.get(role, []) if role else []
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "permissions": [p.value for p in permissions],
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.USER_READ)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.USER_CREATE)),
):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        address=user_data.address,
        role=user_data.role,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.USER_UPDATE)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data:
        user.hashed_password = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.post("/change-role", response_model=UserResponse)
async def change_user_role(
    request: ChangeRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.USER_MANAGE_ROLES)),
):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.id == user.id and user.role == UserRole.ADMIN:
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot change role: You are the only admin",
            )

    user.role = request.new_role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.USER_DELETE)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    if user.role == UserRole.ADMIN:
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the only admin user",
            )

    db.delete(user)
    db.commit()
    return None


@router.get("/{user_id}/permissions", response_model=UserPermissions)
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.USER_READ)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    role = Role(role_value) if role_value in Role._value2member_map_ else None
    permissions = ROLE_PERMISSIONS.get(role, []) if role else []
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "permissions": [p.value for p in permissions],
    }
