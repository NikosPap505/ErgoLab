import logging
from typing import List, Optional
from pathlib import Path

import jinja2
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)


template_loader = jinja2.FileSystemLoader(
    Path(__file__).parent.parent / "templates" / "email"
)
template_env = jinja2.Environment(loader=template_loader, autoescape=True)

email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
    MAIL_STARTTLS=settings.SMTP_TLS,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email",
)

fast_mail = FastMail(email_conf)


class EmailService:
    @staticmethod
    async def send_email(
        recipients: List[EmailStr],
        subject: str,
        body: str = "",
        template_name: Optional[str] = None,
        template_data: Optional[dict] = None,
    ) -> None:
        """Send email using HTML template or plain HTML body."""
        try:
            if template_name and template_data:
                template = template_env.get_template(f"{template_name}.html")
                html_content = template.render(**template_data)
            else:
                html_content = body

            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=html_content,
                subtype="html",
            )

            await fast_mail.send_message(message)
            logger.info("Email sent successfully to %s", recipients)
        except Exception as exc:
            logger.error("Failed to send email: %s", str(exc))
            raise

    @staticmethod
    async def send_low_stock_alert(
        recipient: EmailStr,
        material_name: str,
        sku: str,
        current_quantity: int,
        minimum_quantity: int,
        warehouse_name: str,
    ) -> None:
        """Low stock alert email."""
        await EmailService.send_email(
            recipients=[recipient],
            subject=f"⚠️ Χαμηλό Απόθεμα - {material_name}",
            template_name="low_stock_alert",
            template_data={
                "material_name": material_name,
                "sku": sku,
                "current_quantity": current_quantity,
                "minimum_quantity": minimum_quantity,
                "warehouse_name": warehouse_name,
                "frontend_url": settings.FRONTEND_URL,
            },
        )

    @staticmethod
    async def send_daily_report_summary(
        recipient: EmailStr,
        project_name: str,
        report_date: str,
        workers_count: int,
        progress_percentage: float,
        issues_count: int,
        report_id: int,
    ) -> None:
        """Daily report summary email."""
        await EmailService.send_email(
            recipients=[recipient],
            subject=f"📋 Ημερήσια Αναφορά - {project_name} ({report_date})",
            template_name="daily_report_summary",
            template_data={
                "project_name": project_name,
                "report_date": report_date,
                "workers_count": workers_count,
                "progress_percentage": progress_percentage,
                "issues_count": issues_count,
                "report_id": report_id,
                "frontend_url": settings.FRONTEND_URL,
            },
        )

    @staticmethod
    async def send_issue_assignment(
        recipient: EmailStr,
        issue_title: str,
        project_name: str,
        severity: str,
        assigned_by: str,
        issue_id: int,
    ) -> None:
        """Issue assignment email."""
        severity_labels = {
            "low": "Χαμηλή",
            "medium": "Μεσαία",
            "high": "Υψηλή",
            "critical": "Κρίσιμη",
        }

        await EmailService.send_email(
            recipients=[recipient],
            subject=f"🔴 Νέο Πρόβλημα - {issue_title}",
            template_name="issue_assignment",
            template_data={
                "issue_title": issue_title,
                "project_name": project_name,
                "severity": severity_labels.get(severity, severity),
                "severity_class": severity,
                "assigned_by": assigned_by,
                "issue_id": issue_id,
                "frontend_url": settings.FRONTEND_URL,
            },
        )
