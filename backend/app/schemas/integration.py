"""
AWS and Notification Integration Schemas
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AWSConnectionTestRequest(BaseModel):
    account_id: Optional[str] = None
    role_arn: Optional[str] = None
    external_id: Optional[str] = None
    region: str = "us-east-1"


class AWSConnectionTestResponse(BaseModel):
    is_connected: bool
    account_id_masked: str
    sts_identity_verified: bool
    cost_explorer_accessible: bool
    budgets_accessible: bool
    status_message: str
    timestamp: datetime


class NotificationTestRequest(BaseModel):
    channel_type: str  # email, slack, teams, gchat
    webhook_url: Optional[str] = None
    recipient_email: Optional[str] = None


class NotificationTestResponse(BaseModel):
    success: bool
    channel_type: str
    message: str
    timestamp: datetime

