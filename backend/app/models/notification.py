from sqlalchemy import Boolean, Column, ForeignKey, Integer
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
