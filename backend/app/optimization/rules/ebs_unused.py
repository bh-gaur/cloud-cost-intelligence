"""
OPT-003: Unattached EBS Volumes Rule
Detects EBS volumes in 'available' status not attached to any EC2 instance.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class EBSUnusedRule(BaseOptimizationRule):
    rule_id = "OPT-003"
    name = "Unattached EBS Volumes"
    service = "Amazon Elastic Block Store"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        volumes = inventory.get("ebs_volumes", [])

        for vol in volumes:
            status = vol.get("status")
            if status == "available":
                cost = to_decimal(vol.get("monthly_cost", 0))
                size_gb = vol.get("size_gb", 0)
                savings_m = cost
                savings_a = savings_m * Decimal("12")
                vol_id = vol.get("volume_id", "vol-unknown")

                recs.append(
                    Recommendation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        account_id=account_id,
                        region=region,
                        service=self.service,
                        resource_id=vol_id,
                        resource_name=f"EBS {size_gb}GB ({vol.get('volume_type')})",
                        current_monthly_cost=cost,
                        estimated_monthly_savings=savings_m,
                        estimated_annual_savings=savings_a,
                        savings_percentage=Decimal("100.00"),
                        priority="HIGH",
                        confidence="Observed",
                        validation_status="Requires validation",
                        reason=f"Volume {vol_id} ({size_gb}GB) is in 'available' status and not attached to any instance.",
                        recommendation="Create a final snapshot if data retention is required, then delete the unattached EBS volume.",
                        action_required="Verify volume contents with team owner and delete via AWS Console or CLI.",
                    )
                )

        return recs

