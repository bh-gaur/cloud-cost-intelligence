"""
OPT-004: RDS Rightsizing Rule
Identifies over-provisioned Amazon RDS instances with low CPU and connection activity.
"""

from decimal import Decimal
from typing import Any, Dict, List
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.utils.money import to_decimal


class RDSRightsizingRule(BaseOptimizationRule):
    rule_id = "OPT-004"
    name = "RDS Rightsizing"
    service = "Amazon Relational Database Service"

    def evaluate(
        self, account_id: str, region: str, inventory: Dict[str, Any]
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []
        instances = inventory.get("rds_instances", [])

        for db in instances:
            avg_cpu = db.get("average_cpu", 100.0)
            max_conn = db.get("max_connections", 100)

            if avg_cpu < 15.0 and max_conn < 15:
                cost = to_decimal(db.get("monthly_cost", 0))
                # Downgrading 1 RDS class saves ~40%
                savings_m = (cost * Decimal("0.40")).quantize(Decimal("0.0001"))
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
                        savings_percentage=Decimal("40.00"),
                        priority="MEDIUM",
                        confidence="Estimated",
                        validation_status="Requires validation",
                        reason=f"Database {db_id} has sustained CPU utilization of {avg_cpu:.1f}% with peak connections under {max_conn}.",
                        recommendation=f"Downsize from {db.get('instance_class')} or convert to Aurora Serverless v2.",
                        action_required="Modify the RDS instance type during the weekly maintenance window.",
                    )
                )

        return recs

