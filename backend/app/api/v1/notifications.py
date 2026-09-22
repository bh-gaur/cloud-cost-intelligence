"""
Notification Integrations API Router
Manages external webhooks (Slack, Teams, Google Chat, SMTP) and health testing.
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.integration import NotificationTestRequest, NotificationTestResponse
from app.models.notification import NotificationIntegration
from app.notifications.service import NotificationService
from app.auth.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])
notification_service = NotificationService()


@router.get("/status", response_model=ApiResponse[dict])
def get_notification_status(
    current_user: User = Depends(get_current_user),
):
    """Returns connectivity health status for all notification channels without exposing secrets."""
    statuses = {}
    for ch in ("email", "slack", "teams", "google_chat"):
        statuses[ch] = notification_service.test_connection(ch)
    return ApiResponse.ok(statuses)


from app.config.settings import settings


@router.post("/test", response_model=ApiResponse[NotificationTestResponse])
def test_notification_channel(
    req: NotificationTestRequest,
    current_user: User = Depends(require_admin),
):
    """Validates configuration and dispatches a test alert notification to the specified channel."""
    res = notification_service.test_connection(
        channel=req.channel_type,
        custom_webhook=req.webhook_url,
        recipient_email=req.recipient_email,
    )
    if res.get("healthy", False):
        test_payload = {
            "subject": "AWS Cost Intelligence - Test Alert",
            "html_body": (
                "<div style='font-family: Arial, sans-serif; padding: 20px; border: 1px solid #cbd5e1; border-radius: 8px; max-width: 600px;'>"
                "<h2 style='color: #2563eb; margin-top: 0;'>AWS Cost Intelligence Platform</h2>"
                "<p style='color: #334155; font-size: 15px;'>This is a test alert confirming your SMTP email notification channel is active and operational.</p>"
                "<div style='background-color: #f1f5f9; padding: 12px; border-radius: 6px; font-size: 14px;'>"
                "<strong>Status:</strong> <span style='color: #16a34a;'>Verified & Active</span><br/>"
                "<strong>Recipient:</strong> " + str(settings.EMAIL_RECIPIENTS) + "<br/>"
                "</div>"
                "<p style='color: #64748b; font-size: 12px; margin-top: 20px;'>Sent from AWS Cost Intelligence Platform</p>"
                "</div>"
            ),
        }
        dispatch_res = notification_service.dispatch(req.channel_type, test_payload)
        if dispatch_res.get(req.channel_type):
            res["message"] = f"Test email successfully sent to {settings.EMAIL_RECIPIENTS}"

    return ApiResponse.ok(
        NotificationTestResponse(
            success=res.get("healthy", False),
            channel_type=req.channel_type,
            message=res.get("message", "Test completed."),
            timestamp=datetime.now(timezone.utc),
        )
    )


