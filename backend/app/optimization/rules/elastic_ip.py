"""
OPT-003: Unassociated Elastic IP Addresses Rule
Detects allocated Elastic IP (EIP) addresses not associated with any running EC2 instance or network interface.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class ElasticIPRule(BaseOptimizationRule):
    rule_id = "OPT-003"
    name = "Unassociated Elastic IPs"
    service = "Amazon Elastic Compute Cloud"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        eips = inventory.get("elastic_ips", [])

        for eip in eips:
            assoc_id = eip.get("association_id")
            inst_id = eip.get("instance_id")

            # Unassociated if neither association_id nor instance_id is present
            if not assoc_id and not inst_id:
                cost = to_decimal(eip.get("monthly_cost", Decimal("3.60")))
                savings_m = cost
                savings_a = savings_m * Decimal("12")
                ip_addr = eip.get("public_ip", "eip-unknown")
                alloc_id = eip.get("allocation_id", ip_addr)

                recs.append(
                    Recommendation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        account_id=account_id,
                        region=region,
                        service=self.service,
                        resource_id=alloc_id,
                        resource_name=f"Elastic IP {ip_addr}",
                        current_monthly_cost=cost,
                        estimated_monthly_savings=savings_m,
                        estimated_annual_savings=savings_a,
                        savings_percentage=Decimal("100.00"),
                        priority="LOW",
                        confidence="Observed",
                        validation_status="Requires validation",
                        reason=f"Elastic IP {ip_addr} is allocated but not associated with any running resource, accumulating charges.",
                        recommendation="Release the unassociated Elastic IP address back to the AWS pool if no longer needed.",
                        action_required="Release Elastic IP via AWS Console or CLI: aws ec2 release-address --allocation-id <allocation-id>.",
                    )
                )

        return recs
