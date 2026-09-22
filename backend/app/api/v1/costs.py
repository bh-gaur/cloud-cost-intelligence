"""
Costs Exploration API Router
Searchable, filterable, sortable, paginated cost records table and streaming CSV download.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiMeta, ApiResponse
from app.schemas.cost import CostRecordSchema, CostFilterParams, TagAnalysisResponse
from app.services.cost_service import CostService
from app.providers.factory import get_cloud_provider
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.auth.tenant_context import TenantContext, get_tenant_context
from app.auth.permissions import RequirePermission, PERM_COSTS_EXPORT

router = APIRouter(prefix="/costs", tags=["Cost Exploration"])


def get_cost_service() -> CostService:
    provider = get_cloud_provider()
    return CostService(provider)


@router.get("", response_model=ApiResponse[List[CostRecordSchema]])
def get_costs_table(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=500),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[str] = None,
    service: Optional[str] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    min_cost: Optional[Decimal] = None,
    max_cost: Optional[Decimal] = None,
    search: Optional[str] = None,
    sort_by: str = Query("date"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns filtered and paginated line-item cost records."""
    params = CostFilterParams(
        page=page,
        page_size=page_size,
        organization_id=tenant_ctx.organization_id,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        service=service,
        region=region,
        category=category,
        min_cost=min_cost,
        max_cost=max_cost,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    records, total_count = cost_service.get_cost_records(db, params)
    total_pages = (total_count + page_size - 1) // page_size

    meta = ApiMeta(
        page=page,
        page_size=page_size,
        total_count=total_count,
        total_pages=total_pages,
    )

    return ApiResponse.ok(
        data=[CostRecordSchema.model_validate(r) for r in records],
        meta=meta,
    )


@router.get("/export/csv")
def export_costs_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[str] = None,
    service: Optional[str] = None,
    region: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_COSTS_EXPORT)),
):
    """Streams a CSV file matching the currently applied filters."""
    params = CostFilterParams(
        organization_id=tenant_ctx.organization_id,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        service=service,
        region=region,
        search=search,
    )

    generator = cost_service.export_cost_records_csv(db, params)
    filename = f"aws-costs-export-{date.today().strftime('%Y-%m-%d')}.csv"

    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tag-analysis", response_model=ApiResponse[TagAnalysisResponse])
def get_tag_analysis(
    account_id: str = Query("all"),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Analyzes tagging coverage, untagged spend, and costs by Environment/Team/App."""
    res = cost_service.get_tag_analysis(
        db, account_id=account_id, organization_id=tenant_ctx.organization_id
    )
    return ApiResponse.ok(TagAnalysisResponse(**res))


@router.post("/sync", response_model=ApiResponse[dict])
def sync_live_costs(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    cost_service: CostService = Depends(get_cost_service),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_COSTS_EXPORT)),
):
    """Triggers live cost synchronization from AWS Cost Explorer into local database."""
    today = date.today()
    from datetime import timedelta
    start_date = today - timedelta(days=days)

    inserted = cost_service.sync_costs(
        db, start_date=start_date, end_date=today, organization_id=tenant_ctx.organization_id
    )

    return ApiResponse.ok({
        "message": f"Successfully fetched live costs ({inserted} records updated).",
        "start_date": str(start_date),
        "end_date": str(today),
        "count": inserted,
    })


