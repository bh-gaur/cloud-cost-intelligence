"""
Authentication API Router
Endpoints for user registration, login, token refresh, logout, session management, and password recovery.
"""

import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, Role
from app.models.session import UserSession
from app.models.invitation import PasswordResetToken, EmailVerificationToken
from app.models.organization import Organization, OrganizationMember
from app.schemas.envelope import ApiResponse
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    GoogleAuthRequest,
    TokenResponse,
    UserResponse,
    OrganizationSummary,
    SessionResponse,
)
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    validate_password_strength,
)
from app.auth.dependencies import get_current_user
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_user_response(user: User, db: Session, active_org_id: str = None) -> UserResponse:
    """Helper to assemble UserResponse with organizations and active organization context."""
    memberships = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id, OrganizationMember.status == "ACTIVE")
        .all()
    )

    org_summaries = []
    active_summary = None

    for m in memberships:
        org = db.query(Organization).filter(Organization.id == m.organization_id).first()
        if org and org.status == "ACTIVE":
            summary = OrganizationSummary(
                id=org.id,
                name=org.name,
                slug=org.slug,
                role=m.role,
            )
            org_summaries.append(summary)
            if active_org_id and org.id == active_org_id:
                active_summary = summary

    if not active_summary and org_summaries:
        active_summary = org_summaries[0]

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.name if user.role else "USER",
        is_active=user.is_active,
        status=getattr(user, "status", "ACTIVE"),
        email_verified=getattr(user, "email_verified", False),
        created_at=user.created_at,
        last_login=user.last_login,
        organizations=org_summaries,
        active_organization=active_summary,
    )


@router.post("/register", response_model=ApiResponse[UserResponse])
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user with password strength checks and default organization membership."""
    try:
        validate_password_strength(req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    email_clean = req.email.strip().lower()
    existing = db.query(User).filter(User.email.ilike(email_clean)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    role_name = req.role_name.upper()
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name, description=f"{role_name} Role")
        db.add(role)
        db.commit()
        db.refresh(role)

    new_user = User(
        email=email_clean,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role_id=role.id,
        is_active=True,
        status="ACTIVE",
        email_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create a fresh, isolated organization for the newly registered user
    import re
    raw_org_name = (req.org_name.strip() if req.org_name and req.org_name.strip() else None) or f"{req.full_name or 'User'}'s Organization"
    base_slug = re.sub(r'[^a-z0-9]+', '-', raw_org_name.lower()).strip('-') or "org"
    slug = f"{base_slug}-{secrets.token_hex(4)}"

    new_org = Organization(name=raw_org_name, slug=slug, status="ACTIVE")
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    member = OrganizationMember(
        organization_id=new_org.id,
        user_id=new_user.id,
        role="OWNER",
        status="ACTIVE",
    )
    db.add(member)
    db.commit()

    AuditService.log(
        db=db,
        action="USER_REGISTERED",
        resource_type="USER",
        resource_id=new_user.id,
        user_email=new_user.email,
        organization_id=new_org.id,
    )

    return ApiResponse.ok(_build_user_response(new_user, db))


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(request: Request, req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates user, verifies active status, records session, and returns JWT tokens."""
    email_clean = req.email.strip().lower()
    user = db.query(User).filter(User.email.ilike(email_clean)).first()
    if not user or not verify_password(req.password, user.hashed_password):
        AuditService.log(
            db=db,
            action="LOGIN_FAILED",
            resource_type="USER",
            user_email=req.email,
            status="FAILED",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active or getattr(user, "status", "ACTIVE") in ("DISABLED", "SUSPENDED"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled or suspended. Please contact administrator.",
        )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    role_name = user.role.name if user.role else "USER"
    access_token = create_access_token(subject=user.id, role=role_name)
    refresh_token = create_refresh_token(subject=user.id, role=role_name)

    # Record UserSession in DB for token revocation and session management
    rf_hash = hash_token(refresh_token)
    user_agent = request.headers.get("user-agent", "Unknown")[:250]
    client_ip = request.client.host if request.client else "Unknown"

    session_record = UserSession(
        user_id=user.id,
        refresh_token_hash=rf_hash,
        ip_address=client_ip,
        user_agent=user_agent,
        device_info=user_agent.split(" ")[0] if user_agent else "Browser",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(session_record)
    db.commit()

    first_member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.status == "ACTIVE",
    ).first()
    user_org_id = first_member.organization_id if first_member else None

    AuditService.log(
        db=db,
        action="LOGIN_SUCCESS",
        resource_type="USER",
        resource_id=user.id,
        user_email=user.email,
        organization_id=user_org_id,
    )

    return ApiResponse.ok(
        TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,
        )
    )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refreshes expired access token if refresh token is valid and unrevoked."""
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type.")
        user_id = payload.get("sub")
        role = payload.get("role", "USER")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    rf_hash = hash_token(req.refresh_token)
    session_rec = db.query(UserSession).filter(UserSession.refresh_token_hash == rf_hash).first()
    if session_rec and session_rec.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked.")

    if session_rec:
        session_rec.last_used_at = datetime.now(timezone.utc)
        db.commit()

    new_access_token = create_access_token(subject=user_id, role=role)
    return ApiResponse.ok(
        TokenResponse(
            access_token=new_access_token,
            refresh_token=req.refresh_token,
            token_type="bearer",
            expires_in=3600,
        )
    )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(req: RefreshTokenRequest = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revokes the current refresh token/session."""
    if req and req.refresh_token:
        rf_hash = hash_token(req.refresh_token)
        session_rec = db.query(UserSession).filter(UserSession.refresh_token_hash == rf_hash).first()
        if session_rec:
            session_rec.revoked_at = datetime.now(timezone.utc)
            db.commit()

    AuditService.log(
        db=db,
        action="LOGOUT",
        resource_type="USER",
        resource_id=current_user.id,
        user_email=current_user.email,
    )
    return ApiResponse.ok({"message": "Successfully logged out."})


@router.post("/logout-all", response_model=ApiResponse[dict])
def logout_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revokes all active sessions for the current user across all devices."""
    active_sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.revoked_at.is_(None))
        .all()
    )
    now = datetime.now(timezone.utc)
    for s in active_sessions:
        s.revoked_at = now
    db.commit()

    AuditService.log(
        db=db,
        action="LOGOUT_ALL_SESSIONS",
        resource_type="USER",
        resource_id=current_user.id,
        user_email=current_user.email,
    )
    return ApiResponse.ok({"message": "Successfully logged out of all active sessions."})


@router.get("/sessions", response_model=ApiResponse[list[SessionResponse]])
def list_user_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lists active user sessions."""
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.revoked_at.is_(None))
        .order_by(UserSession.last_used_at.desc())
        .all()
    )

    resp = [
        SessionResponse(
            id=s.id,
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            device_info=s.device_info,
            created_at=s.created_at,
            last_used_at=s.last_used_at,
            is_current=False,
        )
        for s in sessions
    ]
    if resp:
        resp[0].is_current = True

    return ApiResponse.ok(resp)


@router.delete("/sessions/{session_id}", response_model=ApiResponse[dict])
def revoke_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revokes a specific session."""
    session_rec = (
        db.query(UserSession)
        .filter(UserSession.id == session_id, UserSession.user_id == current_user.id)
        .first()
    )
    if not session_rec:
        raise HTTPException(status_code=404, detail="Session not found.")

    session_rec.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return ApiResponse.ok({"message": "Session successfully revoked."})


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_org_id: str = Header(None, alias="X-Organization-ID"),
):
    """Returns profile information for authenticated user including organizations and active organization."""
    return ApiResponse.ok(_build_user_response(current_user, db, active_org_id=x_org_id))


@router.post("/forgot-password", response_model=ApiResponse[dict])
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Initiates password reset flow with single-use token. Prevents account enumeration."""
    email_clean = req.email.strip().lower()
    user = db.query(User).filter(User.email.ilike(email_clean)).first()
    if user:
        token = secrets.token_urlsafe(32)
        token_h = hash_token(token)
        reset_rec = PasswordResetToken(
            user_id=user.id,
            token_hash=token_h,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(reset_rec)
        db.commit()
        AuditService.log(
            db=db,
            action="PASSWORD_RESET_REQUESTED",
            resource_type="USER",
            resource_id=user.id,
            user_email=user.email,
        )

    # Always return identical response to prevent email enumeration
    return ApiResponse.ok(
        {"message": "If an account exists for this email, password reset instructions have been sent."}
    )


@router.post("/reset-password", response_model=ApiResponse[dict])
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Resets user password with valid reset token and invalidates active sessions."""
    try:
        validate_password_strength(req.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token_h = hash_token(req.token)
    reset_rec = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_h,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )

    if not reset_rec:
        raise HTTPException(status_code=400, detail="Invalid, used, or expired password reset token.")

    user = db.query(User).filter(User.id == reset_rec.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.hashed_password = hash_password(req.new_password)
    reset_rec.used_at = datetime.now(timezone.utc)

    # Invalidate active user sessions upon password reset
    active_sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .all()
    )
    now = datetime.now(timezone.utc)
    for s in active_sessions:
        s.revoked_at = now

    db.commit()

    AuditService.log(
        db=db,
        action="PASSWORD_RESET_SUCCESS",
        resource_type="USER",
        resource_id=user.id,
        user_email=user.email,
    )
    return ApiResponse.ok({"message": "Password successfully updated. You may now log in."})


@router.post("/verify-email", response_model=ApiResponse[dict])
def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verifies user email address using token."""
    token_h = hash_token(req.token)
    vt = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token_hash == token_h,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not vt:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")

    user = db.query(User).filter(User.id == vt.user_id).first()
    if user:
        user.email_verified = True
        vt.used_at = datetime.now(timezone.utc)
        db.commit()

    return ApiResponse.ok({"message": "Email address successfully verified."})


@router.get("/config", response_model=ApiResponse[dict])
def get_auth_config():
    """Returns public authentication configuration settings for frontend OAuth integration."""
    import os
    from app.config.settings import settings
    return ApiResponse.ok({
        "google_client_id": settings.GOOGLE_CLIENT_ID or os.getenv("VITE_GOOGLE_CLIENT_ID", ""),
        "demo_mode": settings.DEMO_MODE,
    })


@router.post("/google", response_model=ApiResponse[dict])
def google_auth(req: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticates a user via Google OAuth2 authorization code or ID Token credential.
    Finds or provisions user account & default organization, returning JWT tokens.
    """
    import re
    import urllib.request
    import urllib.parse
    import json
    import logging
    from app.config.settings import settings

    logger = logging.getLogger("aws_cost_intelligence")
    user_info = None
    is_demo_auth = False

    # Option 1: ID Token Credential (Google One Tap / GIS Button)
    if req.credential:
        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "email" in data:
                    user_info = data
        except Exception as e:
            logger.warning(f"Google ID token verification error: {e}")

    # Option 2: Authorization Code (OAuth Redirect Code Exchange)
    if not user_info and req.code:
        if req.code == "demo" or (settings.DEMO_MODE and not settings.GOOGLE_CLIENT_ID):
            # Fallback for demo testing
            is_demo_auth = True
            user_info = {
                "sub": "google-demo-12345",
                "email": "user@cloudcost.local",
                "name": "Sarah FinOps Analyst",
                "picture": "https://lh3.googleusercontent.com/a/default-user=s96-c",
            }
        else:
            try:
                data = urllib.parse.urlencode({
                    "code": req.code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": req.redirect_uri or settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                }).encode("utf-8")
                token_req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
                with urllib.request.urlopen(token_req, timeout=10) as resp:
                    tokens = json.loads(resp.read().decode("utf-8"))
                    access_token = tokens.get("access_token")
                    if access_token:
                        info_req = urllib.request.Request("https://www.googleapis.com/oauth2/v3/userinfo", headers={"Authorization": f"Bearer {access_token}"})
                        with urllib.request.urlopen(info_req, timeout=10) as info_resp:
                            user_info = json.loads(info_resp.read().decode("utf-8"))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Google OAuth exchange failed: {str(e)}")

    if not user_info or not user_info.get("email"):
        raise HTTPException(status_code=400, detail="Invalid Google authentication credential or missing email.")

    google_id = user_info.get("sub")
    email = user_info.get("email").strip().lower()
    full_name = user_info.get("name") or email.split("@")[0]
    avatar_url = user_info.get("picture")

    # Find user by google_id or email
    user = None
    if google_id:
        user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email.ilike(email)).first()

    user_role = db.query(Role).filter(Role.name == "USER").first()
    if not user_role:
        user_role = Role(name="USER", description="Standard User")
        db.add(user_role)
        db.commit()
        db.refresh(user_role)

    if not user:
        oauth_dummy_pass = hash_password(f"google-oauth-sso-{google_id or email}-{secrets.token_hex(16)}")
        user = User(
            email=email,
            hashed_password=oauth_dummy_pass,
            full_name=full_name,
            google_id=google_id,
            avatar_url=avatar_url,
            role_id=user_role.id,
            is_active=True,
            status="ACTIVE",
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Explicit demo auth falls back to demo_org
        demo_org = None
        if is_demo_auth and settings.DEMO_MODE:
            demo_org = db.query(Organization).filter(Organization.slug == "demo-finops-enterprise").first()

        if demo_org:
            m = OrganizationMember(
                organization_id=demo_org.id,
                user_id=user.id,
                role="ADMIN",
                status="ACTIVE",
            )
            db.add(m)
            db.commit()
        else:
            # Create brand-new personal organization for the newly registered Google user
            slug_base = re.sub(r"[^a-z0-9]", "-", email.split("@")[0].lower())[:40]
            slug = f"{slug_base}-{str(user.id)[:6]}"
            org = Organization(
                name=f"{full_name}'s Organization",
                slug=slug,
                status="ACTIVE",
            )
            db.add(org)
            db.commit()
            db.refresh(org)

            m = OrganizationMember(
                organization_id=org.id,
                user_id=user.id,
                role="OWNER",
                status="ACTIVE",
            )
            db.add(m)
            db.commit()
    else:
        if google_id:
            user.google_id = google_id
        if avatar_url:
            user.avatar_url = avatar_url
        user.email_verified = True

        if is_demo_auth and settings.DEMO_MODE:
            demo_org = db.query(Organization).filter(Organization.slug == "demo-finops-enterprise").first()
            if demo_org:
                existing_m = db.query(OrganizationMember).filter(
                    OrganizationMember.organization_id == demo_org.id,
                    OrganizationMember.user_id == user.id
                ).first()
                if not existing_m:
                    db.add(OrganizationMember(
                        organization_id=demo_org.id,
                        user_id=user.id,
                        role="ADMIN",
                        status="ACTIVE",
                    ))
                    db.commit()

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    role_name = user.role.name if user.role else "USER"
    access_token = create_access_token(subject=user.id, role=role_name)
    refresh_token = create_refresh_token(subject=user.id, role=role_name)

    user_resp = _build_user_response(user, db)

    AuditService.log(
        db=db,
        action="GOOGLE_LOGIN",
        resource_type="USER",
        resource_id=user.id,
        user_id=user.id,
        user_email=user.email,
        status="SUCCESS",
        ip_address=request.client.host if request.client else None,
    )

    return ApiResponse.ok({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_resp.model_dump(),
    })
