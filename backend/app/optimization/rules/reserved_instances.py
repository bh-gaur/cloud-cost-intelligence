"""
OPT-011: Reserved Instances Coverage Rule
Identifies continuous RDS and database instances eligible for Reserved Instance pricing.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class ReservedInstancesRule(BaseOptimizationRule):
    rule_id = "OPT-011"
    name = "RDS Reserved Instance Coverage"
    service = "Amazon Relational Database Service"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        rds_instances = inventory.get("rds_instances", [])

        for db in rds_instances:
            cost = to_decimal(db.get("monthly_cost", 0))
            if cost > Decimal("100.0000"):
                # Standard 1-year No Upfront RDS RI delivers ~32% discount
                savings_m = (cost * Decimal("0.32")).quantize(Decimal("0.0001"))
                savings_a = (savings_m * Decimal("12")).quantize(Decimal("0.0001"))
                db_id = db.get("db_instance_id", "rds-unknown")

                recs.append(
                    Recommendation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        account_id=account_id,
                        region=region,
                        service=self.service,
                        resource_id=db_id,
                        resource_name=f"{db_id} ({db.get('instance_class')})",
                        current_monthly_cost=cost,
                        estimated_monthly_savings=savings_m,
                        estimated_annual_savings=savings_a,
                        savings_percentage=Decimal("32.00"),
                        priority="HIGH",
                        confidence="Estimated",
                        validation_status="Requires validation",
                        reason=f"Production database {db_id} runs 24/7 on on-demand pricing without Reserved Instance coverage.",
                        recommendation=f"Purchase a 1-year Standard No Upfront Reserved DB Instance for {db.get('instance_class')}.",
                        action_required="Acquire Reserved Instance via Amazon RDS Console.",
                    )
                )

        return recs

