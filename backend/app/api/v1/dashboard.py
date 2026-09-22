"""
Dashboard API Router
Serves FinOps executive scorecards, daily cost comparisons, and multi-period trends.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    FinOpsKpisResponse,
    CostTrendResponse,
)
from app.services.cost_service import CostService
from app.providers.factory import get_cloud_provider
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.auth.tenant_context import TenantContext, get_tenant_context

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_cost_service() -> CostService:
    provider = get_cloud_provider()
    return CostService(provider)


@router.get("/summary", response_model=ApiResponse[DashboardSummaryResponse])
def get_dashboard_summary(
    account_id: str = Query("all", description="AWS Account ID or 'all'"),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns Today's, Yesterday's, and Day Before Yesterday's cost with percentage variances."""
    summary = cost_service.get_dashboard_summary(
        db, account_id=account_id, organization_id=tenant_ctx.organization_id
    )
    return ApiResponse.ok(summary)


@router.get("/kpis", response_model=ApiResponse[FinOpsKpisResponse])
def get_finops_kpis(
    account_id: str = Query("all"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD) for custom range"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD) for custom range"),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns FinOps executive KPI metrics."""
    kpis = cost_service.get_finops_kpis(
        db,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        organization_id=tenant_ctx.organization_id,
    )
    return ApiResponse.ok(kpis)


@router.get("/trends", response_model=ApiResponse[CostTrendResponse])
def get_cost_trends(
    range: str = Query("30d", description="7d, 14d, 30d, 90d, mtd, or custom"),
    type: str = Query("line", description="line, bar, donut, or scatter"),
    account_id: str = Query("all"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD) for custom range"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD) for custom range"),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns time-series spend data formatted for interactive charting."""
    trends = cost_service.get_cost_trends(
        db,
        range_key=range,
        chart_type=type,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        organization_id=tenant_ctx.organization_id,
    )
    return ApiResponse.ok(trends)

