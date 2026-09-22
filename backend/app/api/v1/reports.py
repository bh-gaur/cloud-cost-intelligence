"""
Reports API Router
Generates CSV, JSON, and print-ready HTML reports, manages local archives, and streams downloads.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.schemas.report import (
    ReportGenerateRequest,
    ReportResponse,
    ScheduleCreateRequest,
    ScheduleResponse,
)
from app.models.report import Report, ReportSchedule
from app.reports.service import ReportService
from app.auth.permissions import (
    RequirePermission,
    PERM_REPORTS_READ,
    PERM_REPORTS_CREATE,
    PERM_REPORTS_DOWNLOAD,
    PERM_REPORTS_DELETE,
)
from app.auth.tenant_context import TenantContext
from app.services.audit_service import AuditService

router = APIRouter(prefix="/reports", tags=["Reports"])
report_service = ReportService()


@router.get("", response_model=ApiResponse[List[ReportResponse]])
def list_reports(
    db: Session = Depends(get_db),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_REPORTS_READ)),
):
    """Lists all previously generated reports for the active tenant."""
    reports = (
        db.query(Report)
        .filter(Report.organization_id == tenant_ctx.organization_id)
        .order_by(Report.created_at.desc())
        .all()
    )
    res = [
        ReportResponse(
            id=r.id,
            name=r.name,
            format=r.format,
            start_date=r.start_date,
            end_date=r.end_date,
            account_id=r.account_id,
            file_size_bytes=r.file_size_bytes,
            status=r.status,
            created_by=r.created_by,
            created_at=r.created_at,
            download_url=f"/api/v1/reports/{r.id}/download",
        )
        for r in reports
    ]
    return ApiResponse.ok(res)


@router.post("/generate", response_model=ApiResponse[ReportResponse])
def generate_report(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_REPORTS_CREATE)),
):
    """Generates a new CSV, JSON, or HTML report and saves to local disk."""
    if req.start_date > req.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must precede or match end_date.",
        )

    try:
        report = report_service.generate_report(
            db=db,
            fmt=req.format,
            start_date=req.start_date,
            end_date=req.end_date,
            account_id=req.account_id,
            user_id=tenant_ctx.user.id,
            custom_name=req.name,
            organization_id=tenant_ctx.organization_id,
        )

        AuditService.log(
            db=db,
            action="REPORT_GENERATED",
            resource_type="REPORT",
            resource_id=report.id,
            user_id=tenant_ctx.user.id,
            user_email=tenant_ctx.user.email,
            organization_id=tenant_ctx.organization_id,
            details={"format": req.format, "name": report.name},
        )

        return ApiResponse.ok(
            ReportResponse(
                id=report.id,
                name=report.name,
                format=report.format,
                start_date=report.start_date,
                end_date=report.end_date,
                account_id=report.account_id,
                file_size_bytes=report.file_size_bytes,
                status=report.status,
                created_by=report.created_by,
                created_at=report.created_at,
                download_url=f"/api/v1/reports/{report.id}/download",
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/{id}/download")
def download_report(
    id: str,
    db: Session = Depends(get_db),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_REPORTS_DOWNLOAD)),
):
    """Safely streams a generated report file to the client."""
    try:
        canonical_path = report_service.resolve_safe_file_path(
            db, id, organization_id=tenant_ctx.organization_id
        )
        AuditService.log(
            db=db,
            action="REPORT_DOWNLOADED",
            resource_type="REPORT",
            resource_id=id,
            user_id=tenant_ctx.user.id,
            user_email=tenant_ctx.user.email,
            organization_id=tenant_ctx.organization_id,
        )
        return FileResponse(
            path=str(canonical_path),
            filename=canonical_path.name,
            media_type="application/octet-stream",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{id}", response_model=ApiResponse[dict])
def delete_report(
    id: str,
    db: Session = Depends(get_db),
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_REPORTS_DELETE)),
):
    """Deletes a report and removes its local file."""
    report = (
        db.query(Report)
        .filter(
            Report.id == id,
            Report.organization_id == tenant_ctx.organization_id,
        )
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    try:
        path = report_service.resolve_safe_file_path(
            db, id, organization_id=tenant_ctx.organization_id
        )
        if path.is_file():
            path.unlink()
    except Exception:
        pass

    db.delete(report)
    db.commit()

    AuditService.log(
        db=db,
        action="REPORT_DELETED",
        resource_type="REPORT",
        resource_id=id,
        user_id=tenant_ctx.user.id,
        user_email=tenant_ctx.user.email,
        organization_id=tenant_ctx.organization_id,
    )

    return ApiResponse.ok({"message": "Report successfully deleted."})

