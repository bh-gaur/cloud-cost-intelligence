"""
OPT-010: Compute Savings Plans Analysis Rule
Evaluates baseline compute spend for 1-year or 3-year commitment discount opportunities.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class SavingsPlansRule(BaseOptimizationRule):
    rule_id = "OPT-010"
    name = "Compute Savings Plans Commitment"
    service = "AWS Savings Plans"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        instances = inventory.get("ec2_instances", [])

        # Calculate steady on-demand spend from running compute instances
        total_monthly_compute = sum(
            to_decimal(i.get("monthly_cost", 0))
            for i in instances
            if i.get("state") == "running"
        )

        if total_monthly_compute > Decimal("500.0000"):
            # 1-year Compute Savings Plan offers ~28% discount on steady baseline
            savings_m = (total_monthly_compute * Decimal("0.28")).quantize(Decimal("0.0001"))
            savings_a = (savings_m * Decimal("12")).quantize(Decimal("0.0001"))

            recs.append(
                Recommendation(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    account_id=account_id,
                    region=region,
                    service=self.service,
                    resource_id=f"savings-plan-opp-{account_id}",
                    resource_name=f"Compute Savings Plan (Account {account_id[-4:]})",
                    current_monthly_cost=total_monthly_compute,
                    estimated_monthly_savings=savings_m,
                    estimated_annual_savings=savings_a,
                    savings_percentage=Decimal("28.00"),
                    priority="HIGH",
                    confidence="Estimated",
                    validation_status="Requires validation",
                    reason=f"Account has ${total_monthly_compute:,.2f}/month in steady on-demand compute spend across EC2 and Lambda.",
                    recommendation="Purchase a 1-year No Upfront Compute Savings Plan covering 70% of baseline hourly spend.",
                    action_required="Model commitment hourly rate in AWS Cost Explorer Savings Plans Recommendation tool.",
                )
            )

        return recs

