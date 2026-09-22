"""
AWS Multi-Account Organizations Breakdown Router
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.cost import AccountBreakdownItem
from app.services.cost_service import CostService
from app.providers.factory import get_cloud_provider
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.auth.tenant_context import TenantContext
from app.auth.permissions import RequirePermission, PERM_AWS_READ

router = APIRouter(prefix="/accounts", tags=["AWS Accounts"])


def get_cost_service() -> CostService:
    provider = get_cloud_provider()
    return CostService(provider)


@router.get("", response_model=ApiResponse[List[AccountBreakdownItem]])
def list_accounts_breakdown(
    range: str = Query("30d"),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_AWS_READ)),
):
    """Returns spending breakdown across all linked AWS accounts."""
    accounts = cost_service.get_accounts_breakdown(
        db, range_key=range, organization_id=tenant_ctx.organization_id
    )
    return ApiResponse.ok([AccountBreakdownItem(**a) for a in accounts])


@router.get("/{account_id}", response_model=ApiResponse[Dict[str, Any]])
def get_account_detail(
    account_id: str,
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_AWS_READ)),
):
    """Returns services and regional spend for a specific account."""
    services = cost_service.get_services_breakdown(
        db, account_id=account_id, range_key="30d", organization_id=tenant_ctx.organization_id
    )
    return ApiResponse.ok({"account_id": account_id, "services": services})

