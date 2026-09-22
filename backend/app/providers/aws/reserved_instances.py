"""
AWS Reserved Instances Analysis Adapter
"""

import logging
from datetime import date
from typing import Any, Dict
from botocore.exceptions import ClientError
from app.providers.aws.client import AWSClientManager
from app.utils.money import to_decimal

logger = logging.getLogger(__name__)


class AWSReservedInstancesAdapter:
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
        self.client = client_manager.get_client("ce", region_override="us-east-1")

    def get_reservation_coverage(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculates RI coverage across compute and database engines."""
        try:
            response = self.client.get_reservation_coverage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d"),
                }
            )
            coverages = response.get("CoveragesByTime", [])
            if coverages:
                total = coverages[0].get("Total", {}).get("CoverageHours", {}).get("CoverageHoursPercentage", "0.0")
                return {"coverage_percentage": to_decimal(total)}
        except ClientError as e:
            logger.warning("Reservation coverage API error: %s", e)
        return {"coverage_percentage": to_decimal(0)}

    def get_reservation_utilization(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculates RI utilization rate."""
        try:
            response = self.client.get_reservation_utilization(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d"),
                }
            )
            total = response.get("Total", {}).get("UtilizationPercentage", "0.0")
            return {"utilization_percentage": to_decimal(total)}
        except ClientError as e:
            logger.warning("Reservation utilization API error: %s", e)
        return {"utilization_percentage": to_decimal(0)}

