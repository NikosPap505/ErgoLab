from typing import Optional

from pydantic import BaseModel, EmailStr


class NotificationPreferencesBase(BaseModel):
    email_low_stock: bool = True
    email_daily_reports: bool = True
    email_issue_assigned: bool = True
    email_budget_alerts: bool = True
    push_low_stock: bool = False
    push_daily_reports: bool = False
    push_issue_assigned: bool = True
    push_budget_alerts: bool = True


class NotificationPreferencesCreate(NotificationPreferencesBase):
    pass


class NotificationPreferencesUpdate(NotificationPreferencesBase):
    pass


class NotificationPreferencesResponse(NotificationPreferencesBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class EmailSendRequest(BaseModel):
    recipients: list[EmailStr]
    subject: str
    body: str
    template_name: Optional[str] = None
    template_data: Optional[dict] = None
