"""
AWS Integration & Diagnostic Router
Provides connection validation, multi-account listing, CloudFormation/Terraform onboarding, and manual synchronization.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.integration import AWSConnectionTestRequest, AWSConnectionTestResponse
from app.providers.factory import get_cloud_provider
from app.services.cost_service import CostService
from app.services.cloudformation import generate_cfn_template, generate_terraform_template, get_manual_instructions
from app.auth.tenant_context import TenantContext, get_tenant_context
from app.auth.dependencies import get_current_user, require_admin
from app.auth.permissions import RequirePermission, PERM_AWS_DELETE, PERM_AWS_CREATE
from app.models.user import User
from app.models.account import CloudAccount, AWSAccount
from app.models.cost import CostRecord
from app.models.alert import AlertEvent
from app.models.optimization import OptimizationRecommendation
from app.services.audit_service import AuditService

router = APIRouter(prefix="/aws", tags=["AWS Integration"])


class AWSConnectAccountRequest(BaseModel):
    account_id: str = Field(min_length=12, max_length=12, pattern=r"^\d{12}$")
    account_name: str = Field(min_length=2, max_length=128)
    role_arn: str = Field(pattern=r"^arn:aws:iam::\d{12}:role/.+$")
    external_id: str
    default_region: str = "us-east-1"


@router.get("/onboarding/templates", response_model=ApiResponse[Dict[str, Any]])
def get_onboarding_templates(
    aws_account_id: Optional[str] = Query(None, description="Optional customer AWS Account ID"),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Returns CloudFormation JSON template, Terraform HCL string, and manual IAM instructions
    tailored with the tenant's unique ExternalID.
    """
    external_id = tenant_ctx.organization_id  # Use organization_id as tenant ExternalId
    cfn = generate_cfn_template(external_id=external_id)
    tf = generate_terraform_template(external_id=external_id, aws_account_id=aws_account_id or "CUSTOMER_ACCOUNT_ID")
    manual = get_manual_instructions(external_id=external_id, aws_account_id=aws_account_id)

    return ApiResponse.ok({
        "external_id": external_id,
        "cloudformation_template": cfn,
        "terraform_template": tf,
        "manual_instructions": manual,
    })


@router.post("/accounts/connect", response_model=ApiResponse[Dict[str, Any]])
def connect_aws_account(
    req: AWSConnectAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_AWS_CREATE)),
):
    """
    Verifies STS AssumeRole permissions for the provided AWS IAM Role ARN and ExternalID,
    then persists the AWS Account into the tenant's organization database records.
    """
    provider = get_cloud_provider()
    result = provider.test_connection(
        account_id=req.account_id,
        role_arn=req.role_arn,
        external_id=req.external_id,
        region=req.default_region,
    )

    if not result.get("is_connected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AWS STS AssumeRole validation failed: {result.get('error', 'Unable to assume role')}",
        )

    # Check if account already exists under organization or elsewhere
    existing = db.query(AWSAccount).filter(AWSAccount.account_id == req.account_id).first()
    if existing and existing.organization_id != tenant_ctx.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This AWS Account ID is already linked to another organization.",
        )

    now = datetime.now(timezone.utc)
    if existing:
        existing.account_name = req.account_name
        existing.role_arn = req.role_arn
        existing.external_id = req.external_id
        existing.default_region = req.default_region
        existing.connection_status = "CONNECTED"
        existing.last_connection_test = now
        existing.status_message = "Successfully assumed role and verified access."
        aws_rec = existing
    else:
        cloud_acc = CloudAccount(
            organization_id=tenant_ctx.organization_id,
            provider="aws",
            name=req.account_name,
            is_active=True,
        )
        db.add(cloud_acc)
        db.commit()
        db.refresh(cloud_acc)

        aws_rec = AWSAccount(
            organization_id=tenant_ctx.organization_id,
            cloud_account_id=cloud_acc.id,
            account_id=req.account_id,
            account_name=req.account_name,
            role_arn=req.role_arn,
            external_id=req.external_id,
            default_region=req.default_region,
            connection_status="CONNECTED",
            last_connection_test=now,
            status_message="Successfully assumed role and verified access.",
        )
        db.add(aws_rec)
        db.commit()
        db.refresh(aws_rec)

    AuditService.log(
        db=db,
        action="AWS_ACCOUNT_CONNECTED",
        resource_type="AWS_ACCOUNT",
        resource_id=req.account_id,
        user_id=current_user.id,
        user_email=current_user.email,
        organization_id=tenant_ctx.organization_id,
        status="SUCCESS",
        details={"account_name": req.account_name, "role_arn": req.role_arn},
    )

    return ApiResponse.ok({
        "id": aws_rec.id,
        "account_id": aws_rec.account_id,
        "account_name": aws_rec.account_name,
        "role_arn": aws_rec.role_arn,
        "connection_status": aws_rec.connection_status,
        "message": "AWS Account successfully verified and linked to organization.",
    })


@router.delete("/accounts/{account_id}", response_model=ApiResponse[dict])
def disconnect_aws_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_AWS_DELETE)),
):
    """Removes an AWS Account linkage from the user's active organization."""
    aws_rec = (
        db.query(AWSAccount)
        .filter(AWSAccount.account_id == account_id, AWSAccount.organization_id == tenant_ctx.organization_id)
        .first()
    )
    if not aws_rec:
        raise HTTPException(status_code=404, detail="AWS Account not found in active organization.")

    if settings.DEMO_MODE and account_id in ["123456789012", "987654321098"]:
        AuditService.log(
            db=db,
            action="AWS_ACCOUNT_DISCONNECT_SIMULATED",
            resource_type="AWS_ACCOUNT",
            resource_id=account_id,
            user_id=current_user.id,
            user_email=current_user.email,
            organization_id=tenant_ctx.organization_id,
            status="SUCCESS",
            details={"message": "Demo mode simulated disconnect"}
        )
        return ApiResponse.ok({"message": f"[Demo Mode] AWS Account {account_id} disconnect simulated successfully. Shared demo account retained."})

    cloud_acc_id = aws_rec.cloud_account_id

    # Purge all cached data records associated with this account and organization
    db.query(CostRecord).filter(
        CostRecord.account_id == account_id,
        CostRecord.organization_id == tenant_ctx.organization_id
    ).delete(synchronize_session=False)

    db.query(AlertEvent).filter(
        AlertEvent.account_id == account_id,
        AlertEvent.organization_id == tenant_ctx.organization_id
    ).delete(synchronize_session=False)

    db.query(OptimizationRecommendation).filter(
        OptimizationRecommendation.account_id == account_id,
        OptimizationRecommendation.organization_id == tenant_ctx.organization_id
    ).delete(synchronize_session=False)

    db.delete(aws_rec)
    if cloud_acc_id:
        cloud_acc = db.query(CloudAccount).filter(CloudAccount.id == cloud_acc_id).first()
        if cloud_acc:
            db.delete(cloud_acc)

    db.commit()

    AuditService.log(
        db=db,
        action="AWS_ACCOUNT_DISCONNECTED",
        resource_type="AWS_ACCOUNT",
        resource_id=account_id,
        user_id=current_user.id,
        user_email=current_user.email,
        organization_id=tenant_ctx.organization_id,
        status="SUCCESS",
    )

    return ApiResponse.ok({"message": f"AWS Account {account_id} disconnected successfully."})


@router.post("/test-connection", response_model=ApiResponse[AWSConnectionTestResponse])
def test_aws_connection(
    req: AWSConnectionTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Tests AWS authentication, STS AssumeRole identity, and Cost Explorer accessibility.
    """
    provider = get_cloud_provider()
    result = provider.test_connection(
        account_id=req.account_id,
        role_arn=req.role_arn,
        external_id=req.external_id,
        region=req.region,
    )

    AuditService.log(
        db=db,
        action="AWS_CONNECTION_TEST",
        resource_type="AWS_ACCOUNT",
        resource_id=req.account_id,
        user_id=current_user.id,
        user_email=current_user.email,
        organization_id=tenant_ctx.organization_id,
        status="SUCCESS" if result["is_connected"] else "FAILED",
        details={"region": req.region, "connected": result["is_connected"]},
    )

    return ApiResponse.ok(AWSConnectionTestResponse(**result))


@router.get("/accounts", response_model=ApiResponse[List[Dict[str, Any]]])
def list_aws_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Lists all linked AWS accounts for the tenant's organization from database or provider."""
    db_accounts = db.query(AWSAccount).filter(AWSAccount.organization_id == tenant_ctx.organization_id).all()
    if db_accounts:
        return ApiResponse.ok([
            {
                "id": a.id,
                "account_id": a.account_id,
                "account_name": a.account_name,
                "role_arn": a.role_arn,
                "external_id": a.external_id,
                "connection_status": a.connection_status,
                "default_region": a.default_region,
                "is_payer_account": a.is_payer_account,
                "last_connection_test": a.last_connection_test,
                "last_sync_at": a.last_sync_at,
            }
            for a in db_accounts
        ])

    from app.config.settings import settings
    if settings.DEMO_MODE:
        provider = get_cloud_provider()
        accounts = provider.get_accounts()
        return ApiResponse.ok(accounts)

    return ApiResponse.ok([])


@router.post("/sync", response_model=ApiResponse[dict])
def trigger_cost_sync(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Triggers incremental cost synchronization for the organization's connected AWS accounts."""
    from app.config.settings import settings
    db_accounts = (
        db.query(AWSAccount)
        .filter(AWSAccount.organization_id == tenant_ctx.organization_id)
        .all()
    )

    if not db_accounts and not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No AWS accounts are connected to this organization. Please connect your AWS account first under 'AWS Accounts'.",
        )

    provider = get_cloud_provider()
    cost_service = CostService(provider)

    today = date.today()
    start_date = today - timedelta(days=days)

    inserted = cost_service.sync_costs(
        db, start_date=start_date, end_date=today, organization_id=tenant_ctx.organization_id
    )

    AuditService.log(
        db=db,
        action="COST_SYNC_TRIGGERED",
        resource_type="COST_RECORDS",
        user_id=current_user.id,
        user_email=current_user.email,
        organization_id=tenant_ctx.organization_id,
        details={"days": days, "records_synced": inserted, "accounts_count": len(db_accounts)},
    )

    return ApiResponse.ok({
        "message": f"Successfully synchronized {inserted} cost records.",
        "start_date": str(start_date),
        "end_date": str(today),
        "count": inserted,
    })
