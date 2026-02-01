import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    assigned_projects = relationship("ProjectAssignment", back_populates="user")
    stock_transactions = relationship("StockTransaction", back_populates="user")
    transfers_created = relationship("Transfer", back_populates="created_by")
    notification_preferences = relationship(
        "NotificationPreferences",
        back_populates="user",
        uselist=False,
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
