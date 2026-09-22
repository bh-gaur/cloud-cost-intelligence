"""
OPT-007: CloudWatch Log Retention Optimization Rule
Identifies CloudWatch log groups with 'Never Expire' retention accumulating stale log bytes.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class CloudWatchRetentionRule(BaseOptimizationRule):
    rule_id = "OPT-007"
    name = "CloudWatch Log Retention"
    service = "Amazon CloudWatch"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        log_groups = inventory.get("log_groups", [])

        for lg in log_groups:
            retention = lg.get("retention_in_days")
            stored_bytes = lg.get("stored_bytes", 0)

            # Never expire retention with substantial logs (> 50GB)
            if retention is None and stored_bytes > 50 * (1024**3):
                cost = to_decimal(lg.get("monthly_cost", 0))
                # Setting 30-day retention typically slashes 70% of historical log storage
                savings_m = (cost * Decimal("0.70")).quantize(Decimal("0.0001"))
                savings_a = (savings_m * Decimal("12")).quantize(Decimal("0.0001"))
                lg_name = lg.get("log_group_name", "lg-unknown")

                recs.append(
                    Recommendation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        account_id=account_id,
                        region=region,
                        service=self.service,
                        resource_id=lg_name,
                        resource_name=lg_name,
                        current_monthly_cost=cost,
                        estimated_monthly_savings=savings_m,
                        estimated_annual_savings=savings_a,
                        savings_percentage=Decimal("70.00"),
                        priority="LOW",
                        confidence="Estimated",
                        validation_status="Requires validation",
                        reason=f"Log group '{lg_name}' has retention set to 'Never Expire', storing {stored_bytes / (1024**3):.1f} GB of data.",
                        recommendation="Configure a retention period (e.g. 30, 60, or 90 days) or export historical logs to S3 Glacier.",
                        action_required="Update log group retention policy in AWS CloudWatch.",
                    )
                )

        return recs

