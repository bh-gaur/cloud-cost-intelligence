"""
OPT-002: EC2 Rightsizing Rule
Identifies instances running well below capacity that can safely downgrade one family tier.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class EC2RightsizingRule(BaseOptimizationRule):
    rule_id = "OPT-002"
    name = "EC2 Rightsizing"
    service = "Amazon Elastic Compute Cloud - Compute"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        instances = inventory.get("ec2_instances", [])

        for inst in instances:
            avg_cpu = inst.get("average_cpu", 100.0)
            peak_cpu = inst.get("peak_cpu", 100.0)
            state = inst.get("state", "stopped")

            # Peak CPU under 30% indicates over-provisioning
            if state == "running" and 5.0 <= avg_cpu < 25.0 and peak_cpu < 35.0:
                cost = to_decimal(inst.get("monthly_cost", 0))
                # Downsizing 1 instance tier typically saves ~50%
                savings_m = (cost * Decimal("0.50")).quantize(Decimal("0.0001"))
                savings_a = (savings_m * Decimal("12")).quantize(Decimal("0.0001"))
                recs.append(
                    Recommendation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        account_id=account_id,
                        region=region,
                        service=self.service,
                        resource_id=inst.get("instance_id", "i-unknown"),
                        resource_name=inst.get("tags", {}).get("Name", inst.get("instance_id")),
                        current_monthly_cost=cost,
                        estimated_monthly_savings=savings_m,
                        estimated_annual_savings=savings_a,
                        savings_percentage=Decimal("50.00"),
                        priority="MEDIUM",
                        confidence="Estimated",
                        validation_status="Requires validation",
                        reason=f"Instance {inst.get('instance_id')} peak CPU is only {peak_cpu:.1f}%, indicating over-provisioned compute capacity.",
                        recommendation=f"Downsize from {inst.get('instance_type')} to the next lower tier (e.g. half vCPUs/memory).",
                        action_required="Schedule a maintenance window to resize the instance.",
                    )
                )

        return recs

