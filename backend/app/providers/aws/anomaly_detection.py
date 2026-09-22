"""
AWS Cost Anomaly Detection Adapter
Integrates with AWS Cost Anomaly Detection service via Cost Explorer API.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List
from botocore.exceptions import ClientError
from app.providers.aws.client import AWSClientManager
from app.utils.money import to_decimal

logger = logging.getLogger(__name__)


class AWSAnomalyDetectionAdapter:
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
        self.client = client_manager.get_client("ce", region_override="us-east-1")

    def get_anomalies(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Retrieves detected cost anomalies from AWS Cost Anomaly Detection."""
        anomalies: List[Dict[str, Any]] = []
        try:
            response = self.client.get_anomalies(
                DateInterval={
                    "StartDate": start_date.strftime("%Y-%m-%d"),
                    "EndDate": end_date.strftime("%Y-%m-%d"),
                }
            )
            for item in response.get("Anomalies", []):
                anomaly_id = item.get("AnomalyId")
                detected_date = item.get("AnomalyStartDate")
                impact = item.get("AnomalyScore", {}).get("CurrentScore", 0)
                root_cause = item.get("RootCauses", [{}])[0] if item.get("RootCauses") else {}
                service = root_cause.get("Service", "Unknown AWS Service")
                account_id = root_cause.get("LinkedAccount", "Unknown Account")
                region = root_cause.get("Region", "global")
                actual_impact = to_decimal(
                    item.get("Impact", {}).get("TotalImpact", 0)
                )

                anomalies.append({
                    "id": anomaly_id,
                    "date": detected_date,
                    "service": service,
                    "account_id": account_id,
                    "region": region,
                    "severity": "CRITICAL" if actual_impact > Decimal("500.00") else "WARNING",
                    "impact_cost": actual_impact,
                    "score": impact,
                    "root_cause": f"Spike detected in {service} in region {region}",
                })
        except ClientError as e:
            logger.warning("AWS Cost Anomaly Detection not enabled or accessible: %s", e)

        return anomalies

