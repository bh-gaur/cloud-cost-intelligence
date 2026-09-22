"""
AWS Services Cost Breakdown Router
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.cost import ServiceBreakdownItem
from app.services.cost_service import CostService
from app.providers.factory import get_cloud_provider
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.auth.tenant_context import TenantContext, get_tenant_context

router = APIRouter(prefix="/services", tags=["Services Breakdown"])


def get_cost_service() -> CostService:
    provider = get_cloud_provider()
    return CostService(provider)


@router.get("", response_model=ApiResponse[List[ServiceBreakdownItem]])
def list_services_breakdown(
    account_id: str = Query("all"),
    range: str = Query("30d"),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns spend, percentage of total, variance, and trend for each AWS service."""
    services = cost_service.get_services_breakdown(
        db, account_id=account_id, range_key=range, organization_id=tenant_ctx.organization_id
    )
    return ApiResponse.ok([ServiceBreakdownItem(**s) for s in services])


@router.get("/{service_name}", response_model=ApiResponse[Dict[str, Any]])
def get_service_drilldown(
    service_name: str,
    account_id: str = Query("all"),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns historical daily costs and regional distribution for a single service."""
    detail = cost_service.get_service_detail(
        db, service_name=service_name, account_id=account_id, organization_id=tenant_ctx.organization_id
    )
    return ApiResponse.ok(detail)

