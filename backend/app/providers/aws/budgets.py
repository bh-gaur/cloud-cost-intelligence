"""
AWS Budgets Adapter
Fetches defined budgets, current actual spend, and forecasts.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List
from botocore.exceptions import ClientError
from app.providers.aws.client import AWSClientManager
from app.utils.money import to_decimal

logger = logging.getLogger(__name__)


class AWSBudgetsAdapter:
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager
        # AWS Budgets endpoint is global and resolved via us-east-1
        self.client = client_manager.get_client("budgets", region_override="us-east-1")

    def describe_budgets(self, account_id: str) -> List[Dict[str, Any]]:
        """Retrieves active AWS budgets for the specified account."""
        budgets: List[Dict[str, Any]] = []
        try:
            response = self.client.describe_budgets(AccountId=account_id)
            for b in response.get("Budgets", []):
                budget_name = b.get("BudgetName", "Unnamed Budget")
                limit_val = b.get("BudgetLimit", {}).get("Amount", "0.0")
                currency = b.get("BudgetLimit", {}).get("Unit", "USD")
                actual_val = b.get("CalculatedSpend", {}).get("ActualSpend", {}).get("Amount", "0.0")
                forecast_val = b.get("CalculatedSpend", {}).get("ForecastedSpend", {}).get("Amount", "0.0")

                limit_dec = to_decimal(limit_val)
                actual_dec = to_decimal(actual_val)
                forecast_dec = to_decimal(forecast_val)

                remaining = max(Decimal("0.0000"), limit_dec - actual_dec)
                pct_consumed = Decimal("0.00")
                if limit_dec > Decimal("0.0000"):
                    pct_consumed = ((actual_dec / limit_dec) * Decimal("100.00")).quantize(Decimal("0.01"))

                # Determine health status
                if pct_consumed > Decimal("100.00"):
                    status = "Exceeded"
                elif pct_consumed >= Decimal("95.00"):
                    status = "Critical"
                elif pct_consumed >= Decimal("80.00"):
                    status = "Warning"
                else:
                    status = "Healthy"

                time_period = b.get("TimePeriod", {})
                start_str = time_period.get("Start")
                end_str = time_period.get("End")
                period_start = date.fromisoformat(start_str[:10]) if start_str else date.today().replace(day=1)
                period_end = date.fromisoformat(end_str[:10]) if end_str else date.today()

                budgets.append({
                    "budget_name": budget_name,
                    "account_id": account_id,
                    "budget_limit": limit_dec,
                    "current_spend": actual_dec,
                    "forecasted_spend": forecast_dec,
                    "remaining_budget": remaining,
                    "percentage_consumed": pct_consumed,
                    "status": status,
                    "currency": currency,
                    "period_start": period_start,
                    "period_end": period_end,
                })
        except ClientError as e:
            logger.warning("AWS Budgets API not accessible or no budgets found: %s", e)

        return budgets

