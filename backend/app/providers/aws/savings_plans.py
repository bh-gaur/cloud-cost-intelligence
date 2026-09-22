"""
AWS Savings Plans Analysis Adapter
"""

import logging
from datetime import date
from typing import Any, Dict, List
from botocore.exceptions import ClientError
from app.providers.aws.client import AWSClientManager
from app.utils.money import to_decimal

logger = logging.getLogger(__name__)


class AWSSavingsPlansAdapter:
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
        self.client = client_manager.get_client("ce", region_override="us-east-1")

    def get_coverage(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculates Savings Plans coverage percentage."""
        try:
            response = self.client.get_savings_plans_coverage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d"),
                }
            )
            coverages = response.get("SavingsPlansCoverages", [])
            if coverages:
                avg_pct = coverages[0].get("Coverage", {}).get("CoveragePercentage", "0.0")
                return {"coverage_percentage": to_decimal(avg_pct)}
        except ClientError as e:
            logger.warning("Savings plans coverage API error: %s", e)
        return {"coverage_percentage": to_decimal(0)}

    def get_utilization(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculates Savings Plans utilization percentage."""
        try:
            response = self.client.get_savings_plans_utilization(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d"),
                }
            )
            total = response.get("Total", {}).get("Utilization", {}).get("UtilizationPercentage", "0.0")
            return {"utilization_percentage": to_decimal(total)}
        except ClientError as e:
            logger.warning("Savings plans utilization API error: %s", e)
        return {"utilization_percentage": to_decimal(0)}

