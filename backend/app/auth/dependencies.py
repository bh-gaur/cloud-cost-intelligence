"""
Authentication Dependencies and Role-Based Access Control Guards
"""

from typing import Optional
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, Role
from app.auth.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token_header: Optional[str] = Depends(oauth2_scheme),
    token_query: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> User:
    """Validates JWT access token (from Authorization header or ?token= query parameter) and retrieves active user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = token_header or token_query
    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is inactive",
        )
    user_status = getattr(user, "status", "ACTIVE") or "ACTIVE"
    if user_status in ("DISABLED", "SUSPENDED"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {user_status.lower()}. Access denied.",
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Enforces ADMIN role for protected operations."""
    if not current_user.role or current_user.role.name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this action",
        )
    return current_user


def require_admin_or_org_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Enforces platform ADMIN role or active Organization OWNER/ADMIN role."""
    if current_user.role and current_user.role.name == "ADMIN":
        return current_user

    from app.models.organization import OrganizationMember
    org_admin = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.role.in_(["OWNER", "ADMIN"]),
            OrganizationMember.status == "ACTIVE",
        )
        .first()
    )
    if org_admin:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Administrative privileges required for this action",
    )

