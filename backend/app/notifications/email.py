"""
SMTP Email Notification Provider
Sends HTML cost summaries with optional file attachments (CSV or HTML reports).
"""

import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.config.settings import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class EmailNotificationProvider(NotificationProvider):
    def __init__(self, recipients: Optional[List[str]] = None):
        self.recipients = recipients or []

    def get_channel_name(self) -> str:
        return "email"

    def _resolve_recipients(self, payload: Optional[Dict[str, Any]] = None) -> List[str]:
        target = []
        if payload and payload.get("recipients"):
            raw = payload["recipients"]
            if isinstance(raw, list):
                target = [str(r).strip() for r in raw if str(r).strip()]
            elif isinstance(raw, str):
                target = [r.strip() for r in raw.split(",") if r.strip()]
        
        if not target and self.recipients:
            if isinstance(self.recipients, list):
                target = [str(r).strip() for r in self.recipients if str(r).strip()]
            elif isinstance(self.recipients, str):
                target = [r.strip() for r in self.recipients.split(",") if r.strip()]

        if not target and settings.EMAIL_RECIPIENTS:
            target = [r.strip() for r in settings.EMAIL_RECIPIENTS.split(",") if r.strip()]

        return target

    def validate_configuration(self, payload: Optional[Dict[str, Any]] = None) -> bool:
        recipients = self._resolve_recipients(payload)
        return bool(settings.SMTP_HOST and recipients)

    def health_check(self) -> Dict[str, Any]:
        if not settings.SMTP_HOST:
            return {"healthy": False, "message": "SMTP host is not configured."}
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            return {"healthy": True, "message": f"Connected to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT}"}
        except Exception as e:
            return {"healthy": False, "message": f"SMTP health check failed: {str(e)}"}

    def send(self, payload: Dict[str, Any], attachment_path: Optional[str] = None) -> bool:
        recipients = self._resolve_recipients(payload)
        if not settings.SMTP_HOST or not recipients:
            logger.warning("Email provider invoked but SMTP_HOST or recipients not configured.")
            return False

        subject = payload.get("subject", "AWS Cost Intelligence Daily Spend Summary")
        html_body = payload.get("html_body", "<p>Daily cloud spend update attached.</p>")

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = ", ".join(recipients)

        msg.attach(MIMEText(html_body, "html"))

        # Optional attachment
        if attachment_path:
            p = Path(attachment_path)
            if p.is_file():
                with open(p, "rb") as f:
                    part = MIMEApplication(f.read(), Name=p.name)
                part["Content-Disposition"] = f'attachment; filename="{p.name}"'
                msg.attach(part)

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, recipients, msg.as_string())
            logger.info("Email sent successfully to %s", recipients)
            return True
        except Exception as e:
            logger.error("Failed to send email notification: %s", e)
            return False


