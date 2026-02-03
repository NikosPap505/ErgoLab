import enum
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, update
from sqlalchemy.orm import relationship, Session

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    WORKER = "worker"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole, name="userrole", create_type=False, values_callable=lambda x: [e.value for e in x]), default=UserRole.WORKER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    phone = Column(String)
    address = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime)
    
    # Account lockout fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class User(Base):
    # ... existing code ...

    def increment_failed_attempts(self, db: Session) -> None:
        """Increment failed login attempts and lock if threshold reached"""
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        
        db.commit()
        db.refresh(self)

    def reset_failed_attempts(self) -> None:
        """Reset failed attempts and unlock account"""
        self.failed_login_attempts = 0
        self.locked_until = None

    assigned_projects = relationship("ProjectAssignment", back_populates="user")
    stock_transactions = relationship("StockTransaction", back_populates="user")
    transfers_created = relationship("Transfer", back_populates="created_by")
    notification_preferences = relationship(
        "NotificationPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    device_tokens = relationship(
        "DeviceToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    created_reports = relationship("DailyReport", back_populates="creator")
    created_issues = relationship(
        "Issue",
        foreign_keys="Issue.reported_by",
        back_populates="reporter",
    )
    assigned_issues = relationship(
        "Issue",
        foreign_keys="Issue.assigned_to",
        back_populates="assigned_user",
    )
