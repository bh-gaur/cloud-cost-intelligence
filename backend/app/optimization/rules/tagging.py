"""
OPT-009: Untagged Resource Compliance Rule
Identifies infrastructure lacking required FinOps cost-allocation tags.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class TaggingComplianceRule(BaseOptimizationRule):
    rule_id = "OPT-009"
    name = "Untagged Resource Allocation Gap"
    service = "AWS General"

    REQUIRED_TAGS = {"Environment", "Team", "Application"}

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        instances = inventory.get("ec2_instances", [])

        for inst in instances:
            tags = inst.get("tags", {})
            missing = self.REQUIRED_TAGS - set(tags.keys())

            if missing:
                cost = to_decimal(inst.get("monthly_cost", 0))
                # Untagged identification produces governance benefit rather than direct cash savings
                inst_id = inst.get("instance_id", "i-unknown")

                recs.append(
                    Recommendation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        account_id=account_id,
                        region=region,
                        service=self.service,
                        resource_id=inst_id,
                        resource_name=inst.get("tags", {}).get("Name", inst_id),
                        current_monthly_cost=cost,
                        estimated_monthly_savings=Decimal("0.0000"),
                        estimated_annual_savings=Decimal("0.0000"),
                        savings_percentage=Decimal("0.00"),
                        priority="MEDIUM",
                        confidence="Potential",
                        validation_status="Requires validation",
                        reason=f"Resource {inst_id} is missing mandatory cost-allocation tags: {', '.join(sorted(missing))}.",
                        recommendation=f"Tag this resource with {', '.join(sorted(missing))} to ensure proper departmental chargebacks.",
                        action_required="Apply tags via AWS Console, CLI, or IaC pipeline (Terraform/CDK).",
                    )
                )

        return recs

