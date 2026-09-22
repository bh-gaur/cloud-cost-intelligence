"""
FinOps Dashboard Summary and Trend Schemas
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel


class CostComparison(BaseModel):
    current_amount: Decimal
    previous_amount: Decimal
    difference: Decimal
    percentage_change: Decimal
    direction: str  # UP, DOWN, FLAT


class DashboardSummaryResponse(BaseModel):
    today_cost: Decimal
    yesterday_cost: Decimal
    previous_day_cost: Decimal
    today_date: Optional[date] = None
    yesterday_date: Optional[date] = None
    previous_day_date: Optional[date] = None
    today_vs_yesterday: CostComparison
    yesterday_vs_previous_day: CostComparison
    currency: str = "USD"
    last_sync_at: Optional[datetime] = None
    data_freshness: str
    account_context: str
    region_context: str
    is_demo_data: bool = True


class FinOpsKpisResponse(BaseModel):
    total_monthly_spend: Decimal
    month_to_date_spend: Decimal
    projected_month_end_spend: Decimal
    potential_monthly_savings: Decimal
    potential_annual_savings: Decimal
    untagged_spend: Decimal
    untagged_percentage: Decimal
    budget_utilization: Decimal
    top_service: str
    top_account: str
    top_region: str
    anomalies_detected: int


class CostTrendPoint(BaseModel):
    date: str
    total_cost: Decimal
    services: Dict[str, Decimal]


class CostTrendResponse(BaseModel):
    range_label: str
    chart_type: str
    points: List[CostTrendPoint]
    service_totals: Dict[str, Decimal]

