"""
Tenant Context Dataclass & Authorization Guards
"""

from dataclasses import dataclass
from typing import List, Optional
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.auth.dependencies import get_current_user


@dataclass
class TenantContext:
    user: User
    organization_id: str
    organization: Organization
    org_role: str
    membership: OrganizationMember

    def has_permission(self, permission: str) -> bool:
        from app.auth.permissions import has_permission as check_perm
        return check_perm(self.org_role, permission)


def get_tenant_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> TenantContext:
    """
    Validates tenant context for every authenticated API request.
    Extracts requested organization from header X-Organization-ID or query parameter.
    Validates that current_user has active membership in requested organization.
    NEVER trusts frontend-supplied tenant ID without database authorization check.
    """
    target_org_id = x_organization_id or request.query_params.get("organization_id")

    if not target_org_id:
        # Default to user's first active organization membership
        membership = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.status == "ACTIVE",
            )
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not associated with any active organization",
            )
        target_org_id = membership.organization_id
    else:
        # Validate explicit organization request
        membership = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == target_org_id,
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.status == "ACTIVE",
            )
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to the requested organization is denied or membership is inactive",
            )

    organization = db.query(Organization).filter(Organization.id == target_org_id).first()
    if not organization or organization.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive or suspended",
        )

    return TenantContext(
        user=current_user,
        organization_id=target_org_id,
        organization=organization,
        org_role=membership.role,
        membership=membership,
    )


class RequireOrgRole:
    """Dependency guard enforcing specific organization-level roles."""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = [r.upper() for r in allowed_roles]

    def __call__(self, tenant_ctx: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if tenant_ctx.org_role.upper() not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of the following organization roles: {', '.join(self.allowed_roles)}",
            )
        return tenant_ctx
