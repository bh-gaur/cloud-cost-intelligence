"""
Organization Members & Invitation Router
Manages member listing, invitations, role modifications, and member removal.
Enforces strict Tenant Isolation, RBAC Permissions, Owner Protection, and Role Escalation Protection.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, Role
from app.models.organization import Organization, OrganizationMember
from app.models.invitation import OrganizationInvitation
from app.schemas.envelope import ApiResponse
from app.schemas.member import (
    MemberResponse,
    MemberUpdateRequest,
    InviteMemberRequest,
    InviteResponse,
    AcceptInviteRequest,
    AcceptInviteRegisterRequest,
)
from app.auth.security import (
    hash_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
)
from app.auth.dependencies import get_current_user
from app.auth.tenant_context import TenantContext, get_tenant_context
from app.auth.permissions import (
    RequirePermission,
    PERM_MEMBERS_READ,
    PERM_MEMBERS_INVITE,
    PERM_MEMBERS_UPDATE,
    PERM_MEMBERS_REMOVE,
    ALL_ROLES,
)
from app.services.audit_service import AuditService

router = APIRouter(tags=["Organization Members"])

ROLE_HIERARCHY = {
    "OWNER": 5,
    "ADMIN": 4,
    "FINOPS_MANAGER": 3,
    "ANALYST": 2,
    "VIEWER": 1,
}


def _is_expired(dt: Optional[datetime]) -> bool:
    if dt is None:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt < datetime.now(timezone.utc)


def _verify_org_access(org_id: str, tenant_ctx: TenantContext):
    """Verifies that the target org_id matches active tenant context."""
    if tenant_ctx.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant operation denied. Active organization mismatch.",
        )


@router.get("/organizations/{organization_id}/members", response_model=ApiResponse[list[MemberResponse]])
def list_members(
    organization_id: str,
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_MEMBERS_READ)),
    db: Session = Depends(get_db),
):
    """Lists members for the specified organization."""
    _verify_org_access(organization_id, tenant_ctx)

    members = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.organization_id == organization_id)
        .all()
    )

    resp = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            resp.append(
                MemberResponse(
                    id=m.id,
                    organization_id=m.organization_id,
                    user_id=m.user_id,
                    email=user.email,
                    full_name=user.full_name,
                    role=m.role,
                    status=m.status,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
            )

    return ApiResponse.ok(resp)


@router.post("/organizations/{organization_id}/members/invite", response_model=ApiResponse[InviteResponse])
def invite_member(
    organization_id: str,
    req: InviteMemberRequest,
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_MEMBERS_INVITE)),
    db: Session = Depends(get_db),
):
    """Invites a user by email to join the organization with a specified role."""
    _verify_org_access(organization_id, tenant_ctx)

    invited_role = req.role.upper()
    if invited_role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role '{req.role}'. Must be one of: {', '.join(ALL_ROLES)}")

    # Role Escalation Protection: Cannot invite with a role higher than caller's role
    caller_level = ROLE_HIERARCHY.get(tenant_ctx.org_role.upper(), 0)
    target_level = ROLE_HIERARCHY.get(invited_role, 0)
    if target_level > caller_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role escalation denied. Cannot invite a user with role '{invited_role}' higher than your role '{tenant_ctx.org_role}'.",
        )

    email_clean = req.email.strip().lower()

    # Check existing membership
    existing_user = db.query(User).filter(User.email.ilike(email_clean)).first()
    if existing_user:
        existing_m = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == existing_user.id,
            )
            .first()
        )
        if existing_m and existing_m.status == "ACTIVE":
            raise HTTPException(status_code=400, detail="User is already an active member of this organization.")

    token = secrets.token_urlsafe(32)
    invitation = OrganizationInvitation(
        organization_id=organization_id,
        email=email_clean,
        role=invited_role,
        token=token,
        status="PENDING",
        invited_by_id=tenant_ctx.user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    AuditService.log(
        db=db,
        action="MEMBER_INVITED",
        resource_type="ORGANIZATION_MEMBER",
        resource_id=invitation.id,
        user_id=tenant_ctx.user.id,
        user_email=tenant_ctx.user.email,
        org_id=organization_id,
        details={"invited_email": email_clean, "role": invited_role},
    )

    invite_link = f"/accept-invite?token={token}"

    # Dispatch invitation email to user's email address
    try:
        from app.notifications.email import EmailNotificationProvider
        org_name = tenant_ctx.organization.name if tenant_ctx.organization else "Organization"
        email_prov = EmailNotificationProvider()
        email_prov.send({
            "recipients": [email_clean],
            "title": f"Invitation to join {org_name} on Cloud Cost Intelligence",
            "message": f"Hello,\n\nYou have been invited to join {org_name} as {invited_role}.\n\nAccept your invitation link:\n{invite_link}\n\nThis token expires in 7 days.",
        })
    except Exception as e:
        pass

    return ApiResponse.ok(
        InviteResponse(
            id=invitation.id,
            organization_id=invitation.organization_id,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            invitation_link=invite_link,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )
    )


@router.get("/organizations/{organization_id}/invitations", response_model=ApiResponse[list[InviteResponse]])
def list_invitations(
    organization_id: str,
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_MEMBERS_READ)),
    db: Session = Depends(get_db),
):
    """
    Lists active invitations for the specified organization.
    Accepted invitations remain visible for 2 days (48 hours) after acceptance, then are automatically removed.
    """
    _verify_org_access(organization_id, tenant_ctx)
    now = datetime.now(timezone.utc)
    two_days_ago = now - timedelta(days=2)

    # 1. Prune/delete accepted invitations older than 2 days (48 hours)
    try:
        db.query(OrganizationInvitation).filter(
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.status == "ACCEPTED",
            OrganizationInvitation.updated_at < two_days_ago,
        ).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()

    # 2. Return PENDING invitations OR ACCEPTED invitations within 2 days
    invitations = (
        db.query(OrganizationInvitation)
        .filter(OrganizationInvitation.organization_id == organization_id)
        .filter(
            (OrganizationInvitation.status == "PENDING")
            | (
                (OrganizationInvitation.status == "ACCEPTED")
                & (OrganizationInvitation.updated_at >= two_days_ago)
            )
        )
        .order_by(OrganizationInvitation.created_at.desc())
        .all()
    )

    return ApiResponse.ok([
        InviteResponse(
            id=inv.id,
            organization_id=inv.organization_id,
            email=inv.email,
            role=inv.role,
            status=inv.status,
            invitation_link=f"/accept-invite?token={inv.token}",
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        )
        for inv in invitations
    ])


@router.delete("/organizations/{organization_id}/invitations/{invitation_id}", response_model=ApiResponse[dict])
def cancel_invitation(
    organization_id: str,
    invitation_id: str,
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_MEMBERS_INVITE)),
    db: Session = Depends(get_db),
):
    """Revokes a pending organization invitation."""
    _verify_org_access(organization_id, tenant_ctx)

    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.organization_id == organization_id,
        )
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found.")

    db.delete(invitation)
    db.commit()

    AuditService.log(
        db=db,
        action="MEMBER_INVITATION_REVOKED",
        resource_type="ORGANIZATION_MEMBER",
        resource_id=invitation_id,
        user_id=tenant_ctx.user.id,
        user_email=tenant_ctx.user.email,
        org_id=organization_id,
        details={"revoked_email": invitation.email},
    )

    return ApiResponse.ok({"message": "Invitation revoked successfully."})


@router.get("/auth/invite-details", response_model=ApiResponse[dict])
def get_invite_details(
    token: str,
    db: Session = Depends(get_db),
):
    """Retrieves invitation metadata by token for the accept-invite preview."""
    invitation = (
        db.query(OrganizationInvitation)
        .filter(OrganizationInvitation.token == token)
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid invitation token.")

    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    is_expired = _is_expired(invitation.expires_at)
    existing_user = db.query(User).filter(User.email.ilike(invitation.email.strip())).first()

    return ApiResponse.ok({
        "id": invitation.id,
        "organization_id": invitation.organization_id,
        "organization_name": org.name if org else "Organization",
        "email": invitation.email,
        "role": invitation.role,
        "status": invitation.status,
        "is_expired": is_expired,
        "user_exists": existing_user is not None,
        "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
    })


@router.post("/auth/accept-invite-register", response_model=ApiResponse[dict])
def accept_invite_and_register(
    req: AcceptInviteRegisterRequest,
    db: Session = Depends(get_db),
):
    """Registers a new user and accepts their invitation in a single seamless operation."""
    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.token == req.token,
            OrganizationInvitation.status == "PENDING",
        )
        .first()
    )
    if not invitation or _is_expired(invitation.expires_at):
        raise HTTPException(status_code=400, detail="Invalid, expired, or already accepted invitation token.")

    try:
        validate_password_strength(req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    email_clean = invitation.email.strip().lower()

    user = db.query(User).filter(User.email.ilike(email_clean)).first()
    if not user:
        user_role = db.query(Role).filter(Role.name == "USER").first()
        if not user_role:
            user_role = Role(name="USER", description="Standard User")
            db.add(user_role)
            db.commit()
            db.refresh(user_role)

        user = User(
            email=email_clean,
            hashed_password=hash_password(req.password),
            full_name=req.full_name.strip(),
            role_id=user_role.id,
            is_active=True,
            status="ACTIVE",
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    existing_m = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )
    if existing_m:
        existing_m.role = invitation.role
        existing_m.status = "ACTIVE"
    else:
        new_m = OrganizationMember(
            organization_id=invitation.organization_id,
            user_id=user.id,
            role=invitation.role,
            status="ACTIVE",
        )
        db.add(new_m)

    invitation.status = "ACCEPTED"
    invitation.updated_at = datetime.now(timezone.utc)
    db.commit()

    role_name = user.role.name if user.role else "USER"
    access_token = create_access_token(subject=user.id, role=role_name)
    refresh_token = create_refresh_token(subject=user.id, role=role_name)

    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()

    AuditService.log(
        db=db,
        action="MEMBER_INVITATION_ACCEPTED_NEW_USER",
        resource_type="ORGANIZATION_MEMBER",
        resource_id=invitation.id,
        user_id=user.id,
        user_email=user.email,
        org_id=invitation.organization_id,
        details={"role": invitation.role},
    )

    return ApiResponse.ok({
        "message": f"Account created! Welcome to {org.name if org else 'the organization'}.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "organization_id": invitation.organization_id,
        "organization_name": org.name if org else "Organization",
        "role": invitation.role,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": role_name,
        },
    })


@router.post("/auth/accept-invite", response_model=ApiResponse[dict])
def accept_invitation(
    req: AcceptInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accepts an organization invitation token."""
    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.token == req.token,
            OrganizationInvitation.status == "PENDING",
        )
        .first()
    )
    if not invitation or _is_expired(invitation.expires_at):
        raise HTTPException(status_code=400, detail="Invalid, expired, or already accepted invitation token.")

    # Check if user email matches invitation email
    if current_user.email.strip().lower() != invitation.email.strip().lower():
        raise HTTPException(
            status_code=403,
            detail=f"Invitation was sent to {invitation.email}, but you are currently signed in as {current_user.email}.",
        )

    existing_m = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )
    if existing_m:
        existing_m.role = invitation.role
        existing_m.status = "ACTIVE"
    else:
        new_m = OrganizationMember(
            organization_id=invitation.organization_id,
            user_id=current_user.id,
            role=invitation.role,
            status="ACTIVE",
        )
        db.add(new_m)

    invitation.status = "ACCEPTED"
    invitation.updated_at = datetime.now(timezone.utc)
    db.commit()

    AuditService.log(
        db=db,
        action="MEMBER_INVITATION_ACCEPTED",
        resource_type="ORGANIZATION_MEMBER",
        resource_id=invitation.id,
        user_id=current_user.id,
        user_email=current_user.email,
        org_id=invitation.organization_id,
        details={"role": invitation.role},
    )

    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()

    return ApiResponse.ok({
        "message": f"Successfully joined {org.name if org else 'organization'}.",
        "organization_id": invitation.organization_id,
        "organization_name": org.name if org else "Organization",
        "role": invitation.role,
    })


@router.patch("/organizations/{organization_id}/members/{member_id}", response_model=ApiResponse[MemberResponse])
def update_member(
    organization_id: str,
    member_id: str,
    req: MemberUpdateRequest,
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_MEMBERS_UPDATE)),
    db: Session = Depends(get_db),
):
    """Updates a member's role or status. Enforces Owner Protection and Role Escalation Protection."""
    _verify_org_access(organization_id, tenant_ctx)

    member = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.id == member_id, OrganizationMember.organization_id == organization_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in organization.")

    caller_level = ROLE_HIERARCHY.get(tenant_ctx.org_role.upper(), 0)

    # 1. Role Escalation Protection
    if req.role:
        new_role = req.role.upper()
        if new_role not in ALL_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role '{req.role}'.")

        target_new_level = ROLE_HIERARCHY.get(new_role, 0)
        if target_new_level > caller_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role escalation denied. Cannot assign role '{new_role}' higher than your role '{tenant_ctx.org_role}'.",
            )

        # Self-role escalation check
        if member.user_id == tenant_ctx.user.id and target_new_level > ROLE_HIERARCHY.get(member.role.upper(), 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role escalation denied. Users cannot elevate their own role privileges.",
            )

        # 2. Owner Protection (demoting an OWNER)
        if member.role == "OWNER" and new_role != "OWNER":
            active_owners_count = (
                db.query(OrganizationMember)
                .filter(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.role == "OWNER",
                    OrganizationMember.status == "ACTIVE",
                    OrganizationMember.id != member.id,
                )
                .count()
            )
            if active_owners_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot demote the last organization OWNER. Transfer ownership to another member first.",
                )

        member.role = new_role

    if req.status:
        new_status = req.status.upper()
        if member.role == "OWNER" and new_status != "ACTIVE":
            active_owners_count = (
                db.query(OrganizationMember)
                .filter(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.role == "OWNER",
                    OrganizationMember.status == "ACTIVE",
                    OrganizationMember.id != member.id,
                )
                .count()
            )
            if active_owners_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot suspend or deactivate the last organization OWNER.",
                )
        member.status = new_status

    db.commit()
    db.refresh(member)

    user = db.query(User).filter(User.id == member.user_id).first()
    AuditService.log(
        db=db,
        action="MEMBER_UPDATED",
        resource_type="ORGANIZATION_MEMBER",
        resource_id=member.id,
        user_email=user.email if user else None,
        org_id=organization_id,
    )

    return ApiResponse.ok(
        MemberResponse(
            id=member.id,
            organization_id=member.organization_id,
            user_id=member.user_id,
            email=user.email if user else "",
            full_name=user.full_name if user else "",
            role=member.role,
            status=member.status,
            created_at=member.created_at,
            updated_at=member.updated_at,
        )
    )


@router.delete("/organizations/{organization_id}/members/{member_id}", response_model=ApiResponse[dict])
def remove_member(
    organization_id: str,
    member_id: str,
    tenant_ctx: TenantContext = Depends(RequirePermission(PERM_MEMBERS_REMOVE)),
    db: Session = Depends(get_db),
):
    """Removes a member from the organization. Enforces Owner Protection."""
    _verify_org_access(organization_id, tenant_ctx)

    member = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.id == member_id, OrganizationMember.organization_id == organization_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in organization.")

    # Owner Protection
    if member.role == "OWNER":
        active_owners_count = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.role == "OWNER",
                OrganizationMember.status == "ACTIVE",
                OrganizationMember.id != member.id,
            )
            .count()
        )
        if active_owners_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last organization OWNER. Transfer ownership first.",
            )

    user = db.query(User).filter(User.id == member.user_id).first()
    user_email = user.email if user else ""

    from app.config.settings import settings
    if settings.DEMO_MODE and user_email in ["admin@cloudcost.local", "user@cloudcost.local"]:
        AuditService.log(
            db=db,
            action="MEMBER_REMOVAL_SIMULATED",
            resource_type="ORGANIZATION_MEMBER",
            resource_id=member_id,
            user_id=tenant_ctx.user_id,
            user_email=tenant_ctx.user_email,
            organization_id=organization_id,
            status="SUCCESS",
            details={"target_email": user_email, "message": "Demo mode simulated member removal"}
        )
        return ApiResponse.ok({"message": f"[Demo Mode] Member {user_email} removal simulated successfully. Default demo user retained."})

    db.delete(member)
    db.flush()

    # If user has no remaining organization memberships, delete the orphan user record
    if user:
        remaining_count = (
            db.query(OrganizationMember)
            .filter(OrganizationMember.user_id == user.id)
            .count()
        )
        if remaining_count == 0 and not user.email.endswith("@cloudcost.local"):
            from app.models.session import UserSession
            from app.models.invitation import OrganizationInvitation, PasswordResetToken, EmailVerificationToken
            db.query(UserSession).filter(UserSession.user_id == user.id).delete()
            db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
            db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).delete()
            db.query(OrganizationInvitation).filter(OrganizationInvitation.invited_by_id == user.id).delete()
            db.delete(user)

    db.commit()

    AuditService.log(
        db=db,
        action="MEMBER_REMOVED",
        resource_type="ORGANIZATION_MEMBER",
        resource_id=member_id,
        user_email=user_email,
        org_id=organization_id,
    )

    return ApiResponse.ok({"message": "Member successfully removed from organization."})
