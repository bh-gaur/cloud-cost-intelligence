"""
Authentication and User Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    org_name: Optional[str] = None
    role_name: str = "ADMIN"  # USER or ADMIN


class UserLoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class OrganizationSummary(BaseModel):
    id: str
    name: str
    slug: str
    role: str

    model_config = {"from_attributes": True}


class GoogleAuthRequest(BaseModel):
    code: Optional[str] = None
    credential: Optional[str] = None
    redirect_uri: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    role: str
    is_active: bool
    status: str = "ACTIVE"
    email_verified: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    organizations: list[OrganizationSummary] = []
    active_organization: Optional[OrganizationSummary] = None

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[str] = None
    created_at: datetime
    last_used_at: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}


class VerifyEmailRequest(BaseModel):
    token: str

