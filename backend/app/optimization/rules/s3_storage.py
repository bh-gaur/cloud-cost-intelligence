"""
OPT-005: S3 Storage Class & Lifecycle Optimization Rule
Identifies large S3 Standard buckets lacking lifecycle policies that qualify for Intelligent-Tiering.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class S3StorageRule(BaseOptimizationRule):
    rule_id = "OPT-005"
    name = "S3 Intelligent-Tiering Opportunity"
    service = "Amazon Simple Storage Service"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        buckets = inventory.get("s3_buckets", [])

        for b in buckets:
            size_gb = b.get("size_gb", 0)
            has_lifecycle = b.get("lifecycle_enabled", False)
            storage_class = b.get("storage_class", "STANDARD")

            # Standard buckets > 5000 GB without lifecycle policies
            if storage_class == "STANDARD" and not has_lifecycle and size_gb > 5000:
                cost = to_decimal(b.get("monthly_cost", 0))
                # Intelligent-Tiering automatically yields ~40-60% savings on infrequently accessed data
                savings_m = (cost * Decimal("0.35")).quantize(Decimal("0.0001"))
                savings_a = (savings_m * Decimal("12")).quantize(Decimal("0.0001"))
                name = b.get("bucket_name", "s3-unknown")

                recs.append(
                    Recommendation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        account_id=account_id,
                        region=region,
                        service=self.service,
                        resource_id=name,
                        resource_name=f"Bucket {name} ({size_gb:,} GB)",
                        current_monthly_cost=cost,
                        estimated_monthly_savings=savings_m,
                        estimated_annual_savings=savings_a,
                        savings_percentage=Decimal("35.00"),
                        priority="MEDIUM",
                        confidence="Potential",
                        validation_status="Requires validation",
                        reason=f"Bucket '{name}' holds {size_gb:,} GB in S3 Standard without any lifecycle transition configuration.",
                        recommendation="Enable S3 Intelligent-Tiering or configure automated lifecycle transition to Glacier Flexible Retrieval.",
                        action_required="Apply S3 lifecycle configuration via Terraform or AWS Management Console.",
                    )
                )

        return recs

