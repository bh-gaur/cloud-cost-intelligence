"""
Optimization Recommendations API Router
Evaluates FinOps rules, filters recommendations, and summarizes potential savings.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.optimization import (
    OptimizationRecommendationResponse,
    PotentialSavingsSummary,
)
from app.models.optimization import OptimizationRecommendation
from app.optimization.engine import OptimizationEngine
from app.providers.factory import get_cloud_provider
from app.auth.tenant_context import TenantContext, get_tenant_context
from app.auth.dependencies import get_current_user
from app.auth.permissions import RequirePermission, PERM_OPTIMIZATION_MANAGE
from app.models.user import User

router = APIRouter(prefix="/optimization", tags=["Cost Optimization"])


def get_engine() -> OptimizationEngine:
    provider = get_cloud_provider()
    return OptimizationEngine(provider)


@router.get("/recommendations", response_model=ApiResponse[List[OptimizationRecommendationResponse]])
def list_recommendations(
    account_id: Optional[str] = None,
    service: Optional[str] = None,
    priority: Optional[str] = None,
    confidence: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns active FinOps optimization recommendations with multi-attribute filtering."""
    q = db.query(OptimizationRecommendation).filter(
        OptimizationRecommendation.organization_id == tenant_ctx.organization_id
    )

    if account_id and account_id != "all":
        q = q.filter(OptimizationRecommendation.account_id == account_id)
    if service and service != "all":
        q = q.filter(OptimizationRecommendation.service == service)
    if priority and priority != "all":
        q = q.filter(OptimizationRecommendation.priority == priority.upper())
    if confidence and confidence != "all":
        q = q.filter(OptimizationRecommendation.confidence == confidence)
    if status and status != "all":
        q = q.filter(OptimizationRecommendation.validation_status == status)

    recs = q.order_by(OptimizationRecommendation.estimated_monthly_savings.desc()).all()
    return ApiResponse.ok([OptimizationRecommendationResponse.model_validate(r) for r in recs])


@router.get("/summary", response_model=ApiResponse[PotentialSavingsSummary])
def get_savings_summary(
    account_id: str = Query("all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns aggregated monthly and annual potential savings."""
    summary = OptimizationEngine.get_summary(
        db, account_id=account_id, organization_id=tenant_ctx.organization_id
    )
    return ApiResponse.ok(PotentialSavingsSummary(**summary))


@router.post("/run", response_model=ApiResponse[dict])
@router.post("/scan", response_model=ApiResponse[dict])
def run_optimization_scan(
    account_id: str = Query("all"),
    db: Session = Depends(get_db),
    engine: OptimizationEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_OPTIMIZATION_MANAGE)),
):
    """Triggers deep live AWS scanning and FinOps optimization engine across all tenant accounts."""
    from app.models.account import AWSAccount, CloudAccount
    has_accounts = (
        db.query(AWSAccount).filter(AWSAccount.organization_id == tenant_ctx.organization_id).count() > 0
        or db.query(CloudAccount).filter(CloudAccount.organization_id == tenant_ctx.organization_id).count() > 0
    )
    if not has_accounts:
        return ApiResponse.ok({
            "message": "No AWS accounts connected to your organization. Optimization scan skipped.",
            "count": 0,
            "total_monthly_savings": 0.0,
        })

    results = engine.run_all(
        db, account_id=account_id, organization_id=tenant_ctx.organization_id
    )
    total_savings = sum(float(r.estimated_monthly_savings or 0) for r in results)
    return ApiResponse.ok({
        "message": f"Scan complete. Discovered {len(results)} cost optimization findings.",
        "count": len(results),
        "total_monthly_savings": total_savings,
    })


