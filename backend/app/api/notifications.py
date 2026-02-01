from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.notification import NotificationPreferences
from app.models.user import User
from app.schemas.notification import (
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
)
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


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


