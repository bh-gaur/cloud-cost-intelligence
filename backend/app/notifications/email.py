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
    def get_channel_name(self) -> str:
        return "email"

    def validate_configuration(self) -> bool:
        return bool(settings.SMTP_HOST and settings.EMAIL_RECIPIENTS)

    def health_check(self) -> Dict[str, Any]:
        if not self.validate_configuration():
            return {"healthy": False, "message": "SMTP host or recipients not configured."}
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
        if not self.validate_configuration():
            logger.warning("Email provider invoked but not configured.")
            return False

        subject = payload.get("subject", "AWS Cost Intelligence Daily Spend Summary")
        html_body = payload.get("html_body", "<p>Daily cloud spend update attached.</p>")
        recipients = [r.strip() for r in (settings.EMAIL_RECIPIENTS or "").split(",") if r.strip()]

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


