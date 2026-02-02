from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationPreferences(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    email_low_stock = Column(Boolean, default=True)
    email_daily_reports = Column(Boolean, default=True)
    email_issue_assigned = Column(Boolean, default=True)
    email_budget_alerts = Column(Boolean, default=True)

    push_low_stock = Column(Boolean, default=False)
    push_daily_reports = Column(Boolean, default=False)
    push_issue_assigned = Column(Boolean, default=True)
    push_budget_alerts = Column(Boolean, default=True)

    user = relationship("User", back_populates="notification_preferences")


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    device_type = Column(String)
    device_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="device_tokens")
