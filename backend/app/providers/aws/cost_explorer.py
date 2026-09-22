"""
AWS Cost Explorer Client Adapter
Fetches daily and dimensional spend data using GetCostAndUsage.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError
from app.providers.aws.client import AWSClientManager
from app.utils.money import to_decimal

logger = logging.getLogger(__name__)


class AWSCostExplorerAdapter:
    """Adapter for AWS Cost Explorer API."""

    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
        # Cost Explorer endpoint is always global in us-east-1
        self.client = client_manager.get_client("ce", region_override="us-east-1")

    def get_cost_and_usage(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calls ce.get_cost_and_usage grouped by SERVICE, LINKED_ACCOUNT, and REGION.
        """
        records: List[Dict[str, Any]] = []
        time_period = {
            "Start": start_date.strftime("%Y-%m-%d"),
            "End": end_date.strftime("%Y-%m-%d"),
        }

        # Filter construction
        filters: List[Dict[str, Any]] = []
        if account_id and account_id != "all":
            filters.append({
                "Dimensions": {
                    "Key": "LINKED_ACCOUNT",
                    "Values": [account_id],
                }
            })
        if region and region != "all" and region != "global":
            filters.append({
                "Dimensions": {
                    "Key": "REGION",
                    "Values": [region],
                }
            })

        filter_arg = {}
        if len(filters) == 1:
            filter_arg = {"Filter": filters[0]}
        elif len(filters) > 1:
            filter_arg = {"Filter": {"And": filters}}

        next_page_token = None

        try:
            while True:
                kwargs = {
                    "TimePeriod": time_period,
                    "Granularity": "DAILY",
                    "Metrics": ["UnblendedCost", "UsageQuantity"],
                    "GroupBy": [
                        {"Type": "DIMENSION", "Key": "SERVICE"},
                        {"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"},
                    ],
                    **filter_arg,
                }
                if next_page_token:
                    kwargs["NextPageToken"] = next_page_token

                response = self.client.get_cost_and_usage(**kwargs)

                for period_result in response.get("ResultsByTime", []):
                    period_date = period_result.get("TimePeriod", {}).get("Start")
                    for group in period_result.get("Groups", []):
                        keys = group.get("Keys", [])
                        service = keys[0] if len(keys) > 0 else "Unknown Service"
                        linked_account = keys[1] if len(keys) > 1 else "Unknown Account"
                        item_region = region if (region and region not in ("all", "global")) else "global"


                        metrics = group.get("Metrics", {})
                        cost_amount = metrics.get("UnblendedCost", {}).get("Amount", "0.0")
                        currency = metrics.get("UnblendedCost", {}).get("Unit", "USD")
                        usage_qty = metrics.get("UsageQuantity", {}).get("Amount", "0.0")
                        usage_unit = metrics.get("UsageQuantity", {}).get("Unit", "Units")

                        records.append({
                            "provider": "aws",
                            "date": period_date,
                            "account_id": linked_account,
                            "account_name": f"Account {linked_account[-4:]}",
                            "region": item_region,
                            "service": service,
                            "service_category": self._categorize_service(service),
                            "cost": to_decimal(cost_amount),
                            "usage_quantity": to_decimal(usage_qty),
                            "usage_unit": usage_unit,
                            "currency": currency,
                            "tags": {},
                            "resource_id": None,
                        })

                next_page_token = response.get("NextPageToken")
                if not next_page_token:
                    break

        except ClientError as e:
            logger.error("Cost Explorer API error: %s", e)
            raise

        return records

    def _categorize_service(self, service_name: str) -> str:
        """Categorizes AWS service into FinOps standard domains."""
        s = service_name.lower()
        if "elastic compute cloud" in s or "ec2" in s or "lightsail" in s:
            return "Compute"
        if "simple storage" in s or "s3" in s or "glacier" in s:
            return "Storage"
        if "relational database" in s or "rds" in s or "dynamodb" in s or "aurora" in s:
            return "Database"
        if "virtual private cloud" in s or "vpc" in s or "nat gateway" in s or "transit gateway" in s or "data transfer" in s or "route 53" in s:
            return "Networking"
        if "elastic kubernetes" in s or "eks" in s or "ecs" in s or "fargate" in s:
            return "Containers"
        if "lambda" in s or "api gateway" in s or "step functions" in s or "sqs" in s or "sns" in s:
            return "Serverless"
        if "cloudwatch" in s or "cloudtrail" in s or "x-ray" in s:
            return "Monitoring"
        if "guardduty" in s or "waf" in s or "shield" in s or "kms" in s or "security hub" in s:
            return "Security"
        if "opensearch" in s or "elasticsearch" in s or "emr" in s or "redshift" in s or "athena" in s:
            return "Analytics"
        return "Other"

