"""
Optimization Recommendation Schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class OptimizationRecommendationResponse(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    account_id: str
    region: str
    service: str
    resource_id: str
    resource_name: Optional[str] = None
    current_monthly_cost: Decimal
    estimated_monthly_savings: Decimal
    estimated_annual_savings: Decimal
    savings_percentage: Decimal
    priority: str
    confidence: str
    validation_status: str
    reason: str
    recommendation: str
    action_required: str
    remediation_code: Optional[str] = None
    implementation_effort: Optional[str] = None
    operational_risk: Optional[str] = None
    production_safety_score: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


from pydantic import BaseModel, Field


class PotentialSavingsSummary(BaseModel):
    total_monthly_savings: Decimal = Decimal("0.00")
    total_annual_savings: Decimal = Decimal("0.00")
    by_priority: dict = Field(default_factory=dict)
    by_confidence: dict = Field(default_factory=dict)
    by_service: dict = Field(default_factory=dict)
    total_recommendations: int = 0


