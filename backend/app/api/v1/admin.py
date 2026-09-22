"""
Administration API Router
User management, audit logging inspection, and system health telemetry.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse, ApiMeta
from app.schemas.auth import UserResponse
from app.models.user import User
from app.models.audit import AuditLog
from app.auth.dependencies import require_admin
from app.config.settings import settings

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.delete("/users/{user_id}", response_model=ApiResponse[dict])
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Permanently deletes a user and purges their organization memberships and sessions."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own active admin account.",
        )

    # Purge organization memberships
    from app.models.organization import OrganizationMember
    db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).delete()

    # Purge sessions, reset tokens, verification tokens, and sent invitations
    from app.models.session import UserSession
    from app.models.invitation import OrganizationInvitation, PasswordResetToken, EmailVerificationToken
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
    db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).delete()
    db.query(OrganizationInvitation).filter(OrganizationInvitation.invited_by_id == user.id).delete()

    user_email = user.email
    db.delete(user)
    db.commit()

    from app.services.audit_service import AuditService
    AuditService.log(
        db=db,
        action="USER_DELETED",
        resource_type="USER",
        resource_id=user_id,
        user_email=user_email,
    )

    return ApiResponse.ok({"message": f"User '{user_email}' permanently deleted."})


@router.get("/users", response_model=ApiResponse[List[UserResponse]])
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Lists registered platform users.
    For demo admin sessions (@cloudcost.local), returns demo accounts only to prevent exposing real user data.
    For real platform admins, returns registered non-demo platform users.
    """
    is_demo_session = admin_user.email.endswith("@cloudcost.local")

    if is_demo_session:
        users = (
            db.query(User)
            .filter(User.email.ilike("%@cloudcost.local"))
            .all()
        )
    else:
        users = (
            db.query(User)
            .filter(~User.email.ilike("%@cloudcost.local"))
            .all()
        )

    res = [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.name if u.role else "USER",
            is_active=u.is_active,
            created_at=u.created_at,
            last_login=u.last_login,
        )
        for u in users
    ]
    return ApiResponse.ok(res)


from app.auth.tenant_context import TenantContext, get_tenant_context

@router.get("/audit-logs", response_model=ApiResponse[List[Dict[str, Any]]])
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    """Returns paginated audit log entries for the active organization."""
    q = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == tenant_ctx.organization_id)
        .order_by(AuditLog.created_at.desc())
    )
    total_count = q.count()
    offset = (page - 1) * page_size
    entries = q.offset(offset).limit(page_size).all()

    data = [
        {
            "id": e.id,
            "organization_id": e.organization_id,
            "action": e.action,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "user_email": e.user_email,
            "status": e.status,
            "ip_address": e.ip_address,
            "details": e.details,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]

    meta = ApiMeta(
        page=page,
        page_size=page_size,
        total_count=total_count,
        total_pages=(total_count + page_size - 1) // page_size if total_count > 0 else 0,
    )
    return ApiResponse.ok(data, meta=meta)


@router.get("/system", response_model=ApiResponse[Dict[str, Any]])
def get_system_health(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Returns runtime system status, report retention configurations, and database state."""
    return ApiResponse.ok({
        "environment": settings.ENVIRONMENT,
        "demo_mode": settings.DEMO_MODE,
        "report_retention_days": settings.REPORT_RETENTION_DAYS,
        "database_url_masked": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "local-sqlite",
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
    })

