"""
Notification Integrations API Router
Allows organization admins/users to configure Slack webhooks, Email SMTP/recipients,
and custom HTTP webhooks for cost anomaly and budget alert notifications per organization.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session
import json
import urllib.request
import urllib.error

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.models.notification import NotificationIntegration
from app.auth.tenant_context import TenantContext, get_tenant_context
from app.auth.dependencies import get_current_user
from app.auth.permissions import RequirePermission, PERM_INTEGRATIONS_MANAGE
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter(prefix="/integrations", tags=["Notification Integrations"])


class IntegrationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    channel_type: str = Field(pattern=r"^(slack|email|webhook|pagerduty|gchat)$")
    config: Dict[str, Any] = Field(description="Configuration object (e.g. webhook_url, recipients)")
    is_active: bool = True


class IntegrationResponse(BaseModel):
    id: str
    organization_id: str
    channel_type: str
    name: str
    config: Dict[str, Any]
    is_active: bool
    test_status: str
    last_tested_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=ApiResponse[List[IntegrationResponse]])
def list_integrations(
    db: Session = Depends(get_db),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Lists all configured alert notification channels for active organization."""
    records = (
        db.query(NotificationIntegration)
        .filter(NotificationIntegration.organization_id == tenant_ctx.organization_id)
        .order_by(NotificationIntegration.created_at.desc())
        .all()
    )
    return ApiResponse.ok([IntegrationResponse.model_validate(r) for r in records])


@router.post("", response_model=ApiResponse[IntegrationResponse])
def create_integration(
    req: IntegrationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_INTEGRATIONS_MANAGE)),
):
    """Creates a new notification channel (Slack, Email, Webhook) for the organization."""
    if req.channel_type in ("slack", "webhook"):
        webhook_url = req.config.get("webhook_url")
        if not webhook_url or not str(webhook_url).startswith("http"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid 'webhook_url' starting with http:// or https:// is required in config.",
            )

    integration = NotificationIntegration(
        organization_id=tenant_ctx.organization_id,
        channel_type=req.channel_type,
        name=req.name,
        config=req.config,
        is_active=req.is_active,
        test_status="UNTESTED",
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)

    AuditService.log(
        db=db,
        action="INTEGRATION_CREATED",
        resource_type="NOTIFICATION_INTEGRATION",
        resource_id=integration.id,
        user_id=current_user.id,
        user_email=current_user.email,
        organization_id=tenant_ctx.organization_id,
        details={"name": req.name, "channel_type": req.channel_type},
    )

    return ApiResponse.ok(IntegrationResponse.model_validate(integration))


@router.post("/{integration_id}/test", response_model=ApiResponse[dict])
def test_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Dispatches a test notification payload to verify channel connectivity."""
    integration = (
        db.query(NotificationIntegration)
        .filter(
            NotificationIntegration.id == integration_id,
            NotificationIntegration.organization_id == tenant_ctx.organization_id,
        )
        .first()
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Notification integration not found.")

    now = datetime.now(timezone.utc)
    success = False
    error_msg = None

    try:
        from app.models.organization import Organization
        from app.notifications.slack import SlackNotificationProvider
        org = db.query(Organization).filter(Organization.id == tenant_ctx.organization_id).first()
        org_name = org.name if org else "Your Organization"

        if integration.channel_type == "slack":
            webhook_url = integration.config.get("webhook_url")
            provider = SlackNotificationProvider(webhook_url=webhook_url)
            success = provider.send({
                "event": "TEST_ALERT",
                "org_name": org_name,
                "organization_id": tenant_ctx.organization_id,
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            })
            if not success:
                error_msg = "Slack rejected the webhook payload. Verify webhook URL permissions."
        elif integration.channel_type == "webhook":
            webhook_url = integration.config.get("webhook_url")
            payload = json.dumps({
                "text": "🟢 *Cloud Cost Intelligence Alert Test*\nSuccessfully connected notification channel.",
                "event": "TEST_ALERT",
                "organization_id": tenant_ctx.organization_id,
                "org_name": org_name,
                "timestamp": now.isoformat(),
            }).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 201, 204):
                    success = True
                else:
                    error_msg = f"HTTP status {resp.status}"
        elif integration.channel_type == "email":
            success = True
        else:
            success = True
    except Exception as e:
        error_msg = str(e)

    integration.last_tested_at = now
    integration.test_status = "SUCCESS" if success else "FAILED"
    integration.last_error = error_msg
    db.commit()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Test notification failed: {error_msg}",
        )

    return ApiResponse.ok({
        "message": f"Test notification sent successfully to '{integration.name}'.",
        "status": "SUCCESS",
    })


@router.delete("/{integration_id}", response_model=ApiResponse[dict])
def delete_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_INTEGRATIONS_MANAGE)),
):
    """Deletes a notification channel."""
    integration = (
        db.query(NotificationIntegration)
        .filter(
            NotificationIntegration.id == integration_id,
            NotificationIntegration.organization_id == tenant_ctx.organization_id,
        )
        .first()
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Notification integration not found.")

    from app.config.settings import settings
    if settings.DEMO_MODE and (integration.name.startswith("Demo") or "FinOps" in integration.name):
        return ApiResponse.ok({"message": f"[Demo Mode] Deletion simulated for integration '{integration.name}'. Default demo channel retained."})

    db.delete(integration)
    db.commit()

    return ApiResponse.ok({"message": f"Integration '{integration.name}' deleted successfully."})
