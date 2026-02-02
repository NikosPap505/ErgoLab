from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.notification import DeviceToken, NotificationPreferences
from app.models.user import User
from app.schemas.notification import (
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
)
from app.services.email_service import EmailService
from app.services.fcm_service import FCMService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class DeviceTokenRegister(BaseModel):
    token: str
    device_type: str
    device_name: Optional[str] = None


class TestNotification(BaseModel):
    title: str
    body: str
    user_id: Optional[int] = None


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's notification preferences."""
    prefs = (
        db.query(NotificationPreferences)
        .filter(NotificationPreferences.user_id == current_user.id)
        .first()
    )

    if not prefs:
        prefs = NotificationPreferences(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return prefs


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user's notification preferences."""
    prefs = (
        db.query(NotificationPreferences)
        .filter(NotificationPreferences.user_id == current_user.id)
        .first()
    )

    if not prefs:
        prefs = NotificationPreferences(user_id=current_user.id)
        db.add(prefs)

    for key, value in preferences.model_dump().items():
        setattr(prefs, key, value)

    db.commit()
    db.refresh(prefs)

    return prefs


@router.post("/test-email")
async def send_test_email(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Send a test email to the current user."""
    if not current_user.email:
        raise HTTPException(status_code=400, detail="Ο χρήστης δεν έχει email")

    background_tasks.add_task(
        EmailService.send_email,
        recipients=[current_user.email],
        subject="🧪 Δοκιμαστικό Email από ErgoLab",
        body=(
            f"<h2>Γεια σου {current_user.full_name}!</h2>"
            "<p>Το email σου λειτουργεί σωστά! ✅</p>"
        ),
    )

    return {"message": "Δοκιμαστικό email στάλθηκε"}


@router.post("/register-device")
async def register_device_token(
    device_data: DeviceTokenRegister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(DeviceToken).filter(DeviceToken.token == device_data.token).first()

    if existing:
        existing.user_id = current_user.id
        existing.device_type = device_data.device_type
        existing.device_name = device_data.device_name
        existing.is_active = True
        existing.last_used_at = datetime.utcnow()
    else:
        device_token = DeviceToken(
            user_id=current_user.id,
            token=device_data.token,
            device_type=device_data.device_type,
            device_name=device_data.device_name,
        )
        db.add(device_token)

    db.commit()

    return {"message": "Device registered successfully"}


@router.delete("/unregister-device/{token}")
async def unregister_device_token(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device_token = (
        db.query(DeviceToken)
        .filter(DeviceToken.token == token, DeviceToken.user_id == current_user.id)
        .first()
    )

    if not device_token:
        raise HTTPException(status_code=404, detail="Token not found")

    device_token.is_active = False
    db.commit()

    return {"message": "Device unregistered successfully"}


@router.get("/my-devices")
async def get_my_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    devices = (
        db.query(DeviceToken)
        .filter(DeviceToken.user_id == current_user.id, DeviceToken.is_active.is_(True))
        .all()
    )

    return [
        {
            "id": device.id,
            "device_type": device.device_type,
            "device_name": device.device_name,
            "created_at": device.created_at,
            "last_used_at": device.last_used_at,
        }
        for device in devices
    ]


@router.post("/test")
async def send_test_notification(
    test_data: TestNotification,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can send test notifications",
        )

    target_user_id = test_data.user_id or current_user.id

    await FCMService.send_to_user(
        db=db,
        user_id=target_user_id,
        title=test_data.title,
        body=test_data.body,
        data={"type": "test"},
        notification_type="general",
    )

    return {"message": "Test notification sent"}


