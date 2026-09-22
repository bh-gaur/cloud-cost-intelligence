"""
Organizations API Router
Manages user organization memberships, organization creation, and tenant switching.
"""

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.envelope import ApiResponse
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.auth.dependencies import get_current_user
from app.auth.tenant_context import TenantContext, get_tenant_context

router = APIRouter(prefix="/organizations", tags=["Organizations"])


class OrganizationMemberSchema(BaseModel):
    organization_id: str
    organization_name: str
    organization_slug: str
    role: str
    status: str


class CreateOrganizationRequest(BaseModel):
    name: str
    slug: Optional[str] = None


class SwitchOrganizationRequest(BaseModel):
    organization_id: str


@router.get("/me", response_model=ApiResponse[List[OrganizationMemberSchema]])
def get_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all organizations the authenticated user belongs to."""
    memberships = (
        db.query(OrganizationMember)
        .join(Organization, OrganizationMember.organization_id == Organization.id)
        .filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.status == "ACTIVE",
            Organization.status == "ACTIVE",
        )
        .all()
    )

    result = [
        OrganizationMemberSchema(
            organization_id=m.organization_id,
            organization_name=m.organization.name,
            organization_slug=m.organization.slug,
            role=m.role,
            status=m.status,
        )
        for m in memberships
    ]
    return ApiResponse.ok(result)


@router.post("", response_model=ApiResponse[OrganizationMemberSchema])
def create_organization(
    req: CreateOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a new organization and assigns current user as OWNER."""
    slug = req.slug or req.name.lower().replace(" ", "-").replace("_", "-")
    
    # Ensure slug uniqueness
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        slug = f"{slug}-{db.query(Organization).count() + 1}"

    org = Organization(name=req.name, slug=slug, status="ACTIVE")
    db.add(org)
    db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role="OWNER",
        status="ACTIVE",
    )
    db.add(member)
    db.commit()
    db.refresh(org)

    return ApiResponse.ok(
        OrganizationMemberSchema(
            organization_id=org.id,
            organization_name=org.name,
            organization_slug=org.slug,
            role="OWNER",
            status="ACTIVE",
        )
    )


@router.post("/switch", response_model=ApiResponse[OrganizationMemberSchema])
def switch_organization(
    req: SwitchOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validates user membership in target organization and returns context."""
    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == req.organization_id,
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.status == "ACTIVE",
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to the target organization",
        )

    org = db.query(Organization).filter(Organization.id == req.organization_id).first()
    if not org or org.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Target organization is inactive or suspended",
        )

    return ApiResponse.ok(
        OrganizationMemberSchema(
            organization_id=org.id,
            organization_name=org.name,
            organization_slug=org.slug,
            role=membership.role,
            status=membership.status,
        )
    )


@router.post("/{organization_id}/switch", response_model=ApiResponse[OrganizationMemberSchema])
def switch_organization_by_id(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validates user membership in target organization and returns context."""
    return switch_organization(SwitchOrganizationRequest(organization_id=organization_id), current_user, db)
