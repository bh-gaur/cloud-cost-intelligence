"""
AWS Regions Cost Breakdown Router
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.cost import RegionBreakdownItem
from app.services.cost_service import CostService
from app.providers.factory import get_cloud_provider
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.auth.tenant_context import TenantContext, get_tenant_context

router = APIRouter(prefix="/regions", tags=["Regions Breakdown"])


def get_cost_service() -> CostService:
    provider = get_cloud_provider()
    return CostService(provider)


@router.get("", response_model=ApiResponse[List[RegionBreakdownItem]])
def list_regions_breakdown(
    range: str = Query("30d"),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns geographical cloud spend distribution across AWS regions."""
    regions = cost_service.get_regions_breakdown(
        db, range_key=range, organization_id=tenant_ctx.organization_id
    )
    return ApiResponse.ok([RegionBreakdownItem(**r) for r in regions])

