"""
OPT-008: Orphaned Snapshots Rule
Flags EBS and RDS manual snapshots older than 90 days.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class SnapshotAgeRule(BaseOptimizationRule):
    rule_id = "OPT-008"
    name = "Orphaned or Aging Snapshots"
    service = "Amazon Elastic Block Store"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        snapshots = inventory.get("snapshots", [])

        for snap in snapshots:
            age = snap.get("age_days", 0)
            if age > 90:
                cost = to_decimal(snap.get("monthly_cost", 0))
                savings_m = cost
                savings_a = savings_m * Decimal("12")
                snap_id = snap.get("snapshot_id", "snap-unknown")

                recs.append(
                    Recommendation(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        account_id=account_id,
                        region=region,
                        service=self.service,
                        resource_id=snap_id,
                        resource_name=f"{snap_id} ({snap.get('volume_size_gb')} GB, {age} days old)",
                        current_monthly_cost=cost,
                        estimated_monthly_savings=savings_m,
                        estimated_annual_savings=savings_a,
                        savings_percentage=Decimal("100.00"),
                        priority="LOW",
                        confidence="Observed",
                        validation_status="Requires validation",
                        reason=f"Snapshot {snap_id} is {age} days old, exceeding standard 90-day retention policies.",
                        recommendation="Review snapshot necessity and delete if no longer required for compliance or rollback.",
                        action_required="Automate snapshot lifecycle with AWS Backup or Data Lifecycle Manager (DLM).",
                    )
                )

        return recs

