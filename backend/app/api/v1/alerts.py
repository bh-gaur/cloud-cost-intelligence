"""
Alerts, Anomaly Detection, and AWS Budgets Router
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.alert import (
    AlertRuleCreateRequest,
    AlertRuleResponse,
    AnomalyEventResponse,
    BudgetResponse,
)
from app.models.alert import AlertRule, AlertEvent, BudgetRecord
from app.alerts.detector import AnomalyDetector
from app.providers.factory import get_cloud_provider
from app.auth.tenant_context import TenantContext, get_tenant_context
from app.auth.dependencies import get_current_user, require_admin
from app.auth.permissions import RequirePermission, PERM_ALERTS_CREATE
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["Alerts & Budgets"])


def get_detector() -> AnomalyDetector:
    provider = get_cloud_provider()
    return AnomalyDetector(provider)


@router.get("", response_model=ApiResponse[List[AlertRuleResponse]])
def list_alert_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Lists configured cost alert rules for the active organization."""
    rules = (
        db.query(AlertRule)
        .filter(AlertRule.organization_id == tenant_ctx.organization_id)
        .all()
    )
    return ApiResponse.ok([AlertRuleResponse.model_validate(r) for r in rules])


@router.post("", response_model=ApiResponse[AlertRuleResponse])
def create_alert_rule(
    req: AlertRuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_ALERTS_CREATE)),
):
    """Creates a new threshold or percentage spike alert rule."""
    rule = AlertRule(
        organization_id=tenant_ctx.organization_id,
        name=req.name,
        alert_type=req.alert_type,
        account_id=req.account_id,
        service=req.service,
        threshold_value=req.threshold_value,
        time_window_days=req.time_window_days,
        notification_channel=req.notification_channel,
        is_enabled=req.is_enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return ApiResponse.ok(AlertRuleResponse.model_validate(rule))


@router.get("/anomalies", response_model=ApiResponse[List[AnomalyEventResponse]])
def list_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Lists detected cost anomalies and sudden spikes for the active organization."""
    events = (
        db.query(AlertEvent)
        .filter(AlertEvent.organization_id == tenant_ctx.organization_id)
        .order_by(AlertEvent.created_at.desc())
        .limit(100)
        .all()
    )
    return ApiResponse.ok([AnomalyEventResponse.model_validate(e) for e in events])


@router.get("/budgets", response_model=ApiResponse[List[BudgetResponse]])
def list_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns synchronized AWS Budgets metrics and consumption health for the active organization."""
    budgets = (
        db.query(BudgetRecord)
        .filter(BudgetRecord.organization_id == tenant_ctx.organization_id)
        .all()
    )
    return ApiResponse.ok([BudgetResponse.model_validate(b) for b in budgets])


@router.post("/scan", response_model=ApiResponse[dict])
def trigger_anomaly_scan(
    db: Session = Depends(get_db),
    detector: AnomalyDetector = Depends(get_detector),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Scans cost history for statistical baseline anomalies and updates budgets."""
    events = detector.detect_daily_anomalies(db, organization_id=tenant_ctx.organization_id)
    detector.sync_budgets(db, organization_id=tenant_ctx.organization_id)
    total_anomalies = (
        db.query(AlertEvent)
        .filter(AlertEvent.organization_id == tenant_ctx.organization_id)
        .count()
    )
    if len(events) > 0:
        msg = f"Scan complete: Found {len(events)} new anomalies ({total_anomalies} total active in timeline)."
    elif total_anomalies > 0:
        msg = f"Scan complete: Verified {total_anomalies} active cost anomalies in your timeline."
    else:
        msg = "Scan complete: Spending is healthy within normal baseline boundaries."

    return ApiResponse.ok({
        "message": msg,
        "anomalies_count": total_anomalies,
        "new_anomalies_count": len(events),
    })

