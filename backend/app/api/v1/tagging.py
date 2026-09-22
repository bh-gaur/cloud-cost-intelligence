"""
Tag Governance & Untagged Resource Explorer API Router
Provides comprehensive visibility into cloud tagging compliance, untagged spend, and remediation scripts.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.tagging import (
    TagGovernanceResponse,
    RemediationGenerateRequest,
    RemediationGenerateResponse,
)
from app.services.tagging_service import TaggingService
from app.auth.tenant_context import TenantContext, get_tenant_context
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tagging", tags=["Tag Governance"])


@router.get("/governance", response_model=ApiResponse[TagGovernanceResponse])
def get_tag_governance(
    account_id: str = Query("all", description="AWS Account ID or 'all'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Returns organization-level tag compliance metrics, service breakdown,
    and a prioritized list of untagged resources with remediation commands.
    """
    service = TaggingService()
    summary = service.get_governance_summary(
        db=db,
        organization_id=tenant_ctx.organization_id,
        account_id=account_id,
    )
    return ApiResponse.ok(summary)


@router.post("/remediation", response_model=ApiResponse[RemediationGenerateResponse])
def generate_remediation_code(
    req: RemediationGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """Generates tailored AWS CLI command and Terraform HCL snippet for tagging a resource."""
    cli_cmd = TaggingService.generate_cli_remediation(
        service=req.service,
        resource_id=req.resource_id,
        region=req.region,
        tags=req.custom_tags,
    )
    tf_snippet = TaggingService.generate_terraform_remediation(
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        tags=req.custom_tags,
    )
    return ApiResponse.ok(
        RemediationGenerateResponse(
            resource_id=req.resource_id,
            cli_command=cli_cmd,
            terraform_snippet=tf_snippet,
        )
    )
