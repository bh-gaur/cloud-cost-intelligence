"""
Report and Schedule Schemas
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    name: Optional[str] = None
    format: str = "html"  # csv, json, html, pdf
    start_date: date
    end_date: date
    account_id: str = "all"



class ReportResponse(BaseModel):
    id: str
    name: str
    format: str
    start_date: date
    end_date: date
    account_id: str
    file_size_bytes: int
    status: str
    created_by: Optional[str] = None
    created_at: datetime
    download_url: str

    model_config = {"from_attributes": True}


class ScheduleCreateRequest(BaseModel):
    name: str
    frequency: str  # daily, weekly, monthly
    format: str = "html"  # csv, json, html
    account_id: str = "all"
    notification_channel: str = "email"
    recipients: str
    is_enabled: bool = True


class ScheduleResponse(BaseModel):
    id: str
    name: str
    frequency: str
    format: str
    account_id: str
    notification_channel: str
    recipients: str
    is_enabled: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}

