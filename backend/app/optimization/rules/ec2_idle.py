"""
OPT-001: EC2 Idle Instances Rule
Flags compute instances with sustained average CPU utilization < 5%.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class EC2IdleRule(BaseOptimizationRule):
    rule_id = "OPT-001"
    name = "EC2 Idle Instances"
    service = "Amazon Elastic Compute Cloud - Compute"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        instances = inventory.get("ec2_instances", [])

        for inst in instances:
            avg_cpu = inst.get("average_cpu", 100.0)
            state = inst.get("state", "stopped")
            if state == "running" and avg_cpu < 5.0:
                cost = to_decimal(inst.get("monthly_cost", 0))
                # Stopping/terminating saves 100% of compute fee
                savings_m = cost
                savings_a = savings_m * Decimal("12")
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
                        savings_percentage=Decimal("100.00"),
                        priority="HIGH",
                        confidence="Observed",
                        validation_status="Requires validation",
                        reason=f"Instance {inst.get('instance_id')} averaged {avg_cpu:.1f}% CPU utilization over the monitoring window.",
                        recommendation="Stop or terminate this underutilized compute instance, or migrate tasks to a shared cluster.",
                        action_required="Inspect application owners via tags and shut down the instance during off-hours.",
                    )
                )

        return recs

