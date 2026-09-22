"""
Schemas for Organization Member Management and Invitations
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MemberResponse(BaseModel):
    id: str
    organization_id: str
    user_id: str
    email: str
    full_name: Optional[str] = None
    role: str  # OWNER, ADMIN, FINOPS_MANAGER, ANALYST, VIEWER
    status: str  # ACTIVE, INVITED, SUSPENDED
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberUpdateRequest(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None


class InviteMemberRequest(BaseModel):
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    role: str = "ANALYST"  # OWNER, ADMIN, FINOPS_MANAGER, ANALYST, VIEWER


class InviteResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    role: str
    status: str
    invitation_link: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AcceptInviteRequest(BaseModel):
    token: str


class AcceptInviteRegisterRequest(BaseModel):
    token: str
    full_name: str
    password: str

