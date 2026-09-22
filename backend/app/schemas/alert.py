"""
Alert, Anomaly, and Budget Schemas
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class AlertRuleCreateRequest(BaseModel):
    name: str
    alert_type: str  # DAILY_THRESHOLD, PERCENT_INCREASE, SERVICE_SPIKE, BUDGET_THRESHOLD
    account_id: str = "all"
    service: str = "all"
    threshold_value: Decimal
    time_window_days: int = 1
    notification_channel: str = "all"
    is_enabled: bool = True


class AlertRuleResponse(BaseModel):
    id: str
    name: str
    alert_type: str
    account_id: str
    service: str
    threshold_value: Decimal
    time_window_days: int
    notification_channel: str
    is_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AnomalyEventResponse(BaseModel):
    id: str
    title: str
    severity: str
    account_id: str
    service: Optional[str] = None
    detected_value: Decimal
    expected_value: Optional[Decimal] = None
    difference_percentage: Optional[Decimal] = None
    message: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetResponse(BaseModel):
    id: str
    budget_name: str
    account_id: str
    budget_limit: Decimal
    current_spend: Decimal
    forecasted_spend: Decimal
    remaining_budget: Decimal
    percentage_consumed: Decimal
    status: str
    currency: str
    period_start: date
    period_end: date
    updated_at: datetime

    model_config = {"from_attributes": True}

