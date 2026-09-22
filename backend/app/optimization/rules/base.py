"""
Base Optimization Rule Interface
All FinOps optimization rules must implement this contract.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Recommendation(BaseModel):
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
    priority: str  # HIGH, MEDIUM, LOW
    confidence: str  # Observed, Estimated, Potential
    validation_status: str  # Requires validation, Insufficient data, Validated, Dismissed
    reason: str
    recommendation: str
    action_required: str


class BaseOptimizationRule(ABC):
    rule_id: str = "OPT-000"
    name: str = "Base Rule"
    service: str = "AWS General"

    @abstractmethod
    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        """Evaluates resource telemetry and emits standardized recommendations."""
        pass

