import os
from typing import Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session

from app.models.notification import DeviceToken, NotificationPreferences
from app.models.user import User


class FCMService:
    _initialized = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return

        cred_path = os.getenv("FIREBASE_CREDENTIALS", "firebase-credentials.json")
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            print("✓ Firebase Admin SDK initialized")
        except Exception as e:
            print(f"✗ Error initializing Firebase: {e}")

    @classmethod
    def _ensure_initialized(cls) -> bool:
        if cls._initialized:
            return True
        cls.initialize()
        return cls._initialized

    @staticmethod
    async def send_notification(
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict] = None,
        priority: str = "high",
        channel_id: str = "default",
    ):
        if not tokens:
            return None

        if not FCMService._ensure_initialized():
            return None

        notification = messaging.Notification(title=title, body=body)

        android_config = messaging.AndroidConfig(
            priority=priority,
            notification=messaging.AndroidNotification(
                channel_id=channel_id,
                sound="default",
                color="#667eea",
                icon="ic_notification",
            ),
        )

        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound="default",
                    badge=1,
                )
            )
        )

        message = messaging.MulticastMessage(
            notification=notification,
            data=data or {},
            tokens=tokens,
            android=android_config,
            apns=apns_config,
        )

        try:
            response = messaging.send_multicast(message)

            print(f"✓ Sent {response.success_count} notifications successfully")
            if response.failure_count > 0:
                print(f"✗ Failed to send {response.failure_count} notifications")
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        print(f"  Token {idx}: {resp.exception}")

            return response
        except Exception as e:
            print(f"✗ Error sending notification: {e}")
            return None

    @staticmethod
    async def send_to_user(
        db: Session,
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        notification_type: str = "general",
    ):
        prefs = (
            db.query(NotificationPreferences)
            .filter(NotificationPreferences.user_id == user_id)
            .first()
        )

        if not prefs:
            return None

        pref_map = {
            "daily_report": prefs.push_daily_reports,
            "issue": prefs.push_issue_assigned,
            "stock": prefs.push_low_stock,
            "project": prefs.push_budget_alerts,
            "general": True,
        }

        if notification_type in pref_map and not pref_map[notification_type]:
            return None

        device_tokens = (
            db.query(DeviceToken)
            .filter(DeviceToken.user_id == user_id, DeviceToken.is_active.is_(True))
            .all()
        )

        if not device_tokens:
            return None

        tokens = [dt.token for dt in device_tokens]

        return await FCMService.send_notification(
            tokens=tokens,
            title=title,
            body=body,
            data=data,
        )

    @staticmethod
    async def send_to_role(
        db: Session,
        role: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        exclude_user: Optional[int] = None,
    ):
        users = db.query(User).filter(User.role == role, User.is_active.is_(True))

        if exclude_user:
            users = users.filter(User.id != exclude_user)

        users = users.all()

        all_tokens: List[str] = []
        for user in users:
            device_tokens = (
                db.query(DeviceToken)
                .filter(DeviceToken.user_id == user.id, DeviceToken.is_active.is_(True))
                .all()
            )
            all_tokens.extend([dt.token for dt in device_tokens])

        if not all_tokens:
            return None

        return await FCMService.send_notification(
            tokens=all_tokens,
            title=title,
            body=body,
            data=data,
        )

    @staticmethod
    async def send_critical_alert(
        db: Session,
        title: str,
        body: str,
        data: Optional[Dict] = None,
    ):
        users = (
            db.query(User)
            .filter(User.role.in_(["admin", "manager"]), User.is_active.is_(True))
            .all()
        )

        all_tokens: List[str] = []
        for user in users:
            device_tokens = (
                db.query(DeviceToken)
                .filter(DeviceToken.user_id == user.id, DeviceToken.is_active.is_(True))
                .all()
            )
            all_tokens.extend([dt.token for dt in device_tokens])

        if not all_tokens:
            return None

        return await FCMService.send_notification(
            tokens=all_tokens,
            title=f"🚨 {title}",
            body=body,
            data=data,
            priority="high",
            channel_id="critical_alerts",
        )


FCMService.initialize()
