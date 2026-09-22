"""
Cost Exploration & Breakdown Schemas
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CostRecordSchema(BaseModel):
    id: str
    provider: str
    date: date
    account_id: str
    account_name: str
    region: str
    service: str
    service_category: str
    resource_id: Optional[str] = None
    usage_quantity: Decimal
    usage_unit: str
    cost: Decimal
    currency: str
    tags: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class CostFilterParams(BaseModel):
    page: int = 1
    page_size: int = 25
    organization_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_id: Optional[str] = None
    service: Optional[str] = None
    region: Optional[str] = None
    category: Optional[str] = None
    min_cost: Optional[Decimal] = None
    max_cost: Optional[Decimal] = None
    search: Optional[str] = None
    tag_key: Optional[str] = None
    tag_value: Optional[str] = None
    sort_by: str = "date"  # date, cost, service, account_id
    sort_order: str = "desc"  # asc, desc


class ServiceBreakdownItem(BaseModel):
    service: str
    category: str
    current_cost: Decimal
    percentage_of_total: Decimal
    previous_cost: Decimal
    difference: Decimal
    percentage_change: Decimal
    trend: str  # up, down, flat


class AccountBreakdownItem(BaseModel):
    account_id: str
    account_name: str
    monthly_cost: Decimal
    daily_cost: Decimal
    difference: Decimal
    percentage_of_total: Decimal
    trend: str


class RegionBreakdownItem(BaseModel):
    region: str
    cost: Decimal
    percentage_of_total: Decimal
    difference: Decimal
    trend: str


class TagCategorySummary(BaseModel):
    key: str
    values: Dict[str, Decimal]


class TagAnalysisResponse(BaseModel):
    tagged_cost: Decimal
    untagged_cost: Decimal
    tagging_coverage_percentage: Decimal
    by_environment: Dict[str, Decimal]
    by_team: Dict[str, Decimal]
    by_application: Dict[str, Decimal]
    by_project: Dict[str, Decimal]

