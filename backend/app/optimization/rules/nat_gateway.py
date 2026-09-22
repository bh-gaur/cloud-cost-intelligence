"""
OPT-006: NAT Gateway Optimization Rule
Flags idle or low-throughput NAT Gateways accumulating hourly provisioning charges.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class NATGatewayRule(BaseOptimizationRule):
    rule_id = "OPT-006"
    name = "Idle NAT Gateway Optimization"
    service = "Amazon Virtual Private Cloud"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        nat_gateways = inventory.get("nat_gateways", [])

        for nat in nat_gateways:
            processed_gb = nat.get("bytes_processed_daily_gb", 100.0)
            if processed_gb < 1.0:
                cost = to_decimal(nat.get("monthly_cost", Decimal("32.40")))
                savings_m = cost
                savings_a = savings_m * Decimal("12")
                nat_id = nat.get("nat_gateway_id", "nat-unknown")

                recs.append(
                    Recommendation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        account_id=account_id,
                        region=region,
                        service=self.service,
                        resource_id=nat_id,
                        resource_name=f"{nat_id} in {nat.get('vpc_id', 'VPC')}",
                        current_monthly_cost=cost,
                        estimated_monthly_savings=savings_m,
                        estimated_annual_savings=savings_a,
                        savings_percentage=Decimal("100.00"),
                        priority="LOW",
                        confidence="Observed",
                        validation_status="Requires validation",
                        reason=f"NAT Gateway {nat_id} processed only {processed_gb} GB/day while incurring baseline $0.045/hour charges.",
                        recommendation="Consider replacing with VPC Endpoints for AWS services (S3/DynamoDB) or consolidating subnets.",
                        action_required="Audit subnet route tables and decommission unneeded NAT Gateways.",
                    )
                )

        return recs
