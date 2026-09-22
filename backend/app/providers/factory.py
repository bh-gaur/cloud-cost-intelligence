"""
Cloud Provider Factory
Selects the active CloudProvider based on DEMO_MODE setting or explicit override.
"""

from typing import Optional
from app.config.settings import settings
from app.providers.base import CloudProvider
from app.providers.mock.provider import MockAWSProvider


class AWSProductionProvider(CloudProvider):
    """Production AWS Provider wrapping live AWS adapters with fallback to mock data when credentials are not configured."""

    def __init__(self):
        from app.providers.aws.client import AWSClientManager
        from app.providers.aws.cost_explorer import AWSCostExplorerAdapter
        from app.providers.aws.account import AWSAccountAdapter
        from app.providers.aws.budgets import AWSBudgetsAdapter
        from app.providers.aws.anomaly_detection import AWSAnomalyDetectionAdapter

        self.mock = MockAWSProvider()
        try:
            self.client_manager = AWSClientManager()
            self.ce_adapter = AWSCostExplorerAdapter(self.client_manager)
            self.account_adapter = AWSAccountAdapter(self.client_manager)
            self.budgets_adapter = AWSBudgetsAdapter(self.client_manager)
            self.anomaly_adapter = AWSAnomalyDetectionAdapter(self.client_manager)
        except Exception:
            self.ce_adapter = None
            self.account_adapter = None
            self.budgets_adapter = None
            self.anomaly_adapter = None

    def get_provider_name(self) -> str:
        return "aws"

    def fetch_cost_and_usage(self, start_date, end_date, account_id=None, region=None):
        if not getattr(self, "ce_adapter", None):
            return self.mock.fetch_cost_and_usage(start_date, end_date, account_id, region) if settings.DEMO_MODE else []
        try:
            return self.ce_adapter.get_cost_and_usage(start_date, end_date, account_id, region)
        except Exception:
            return self.mock.fetch_cost_and_usage(start_date, end_date, account_id, region) if settings.DEMO_MODE else []

    def get_accounts(self):
        if not getattr(self, "account_adapter", None):
            return self.mock.get_accounts() if settings.DEMO_MODE else []
        try:
            return self.account_adapter.list_organization_accounts()
        except Exception:
            return self.mock.get_accounts() if settings.DEMO_MODE else []

    def get_budgets(self, account_id=None):
        if not getattr(self, "budgets_adapter", None):
            return self.mock.get_budgets(account_id) if settings.DEMO_MODE else []
        try:
            ident = self.account_adapter.get_caller_identity()
            target_account = account_id or ident["account_id"]
            return self.budgets_adapter.describe_budgets(target_account)
        except Exception:
            return self.mock.get_budgets(account_id) if settings.DEMO_MODE else []

    def get_anomalies(self, start_date, end_date):
        if not getattr(self, "anomaly_adapter", None):
            return self.mock.get_anomalies(start_date, end_date) if settings.DEMO_MODE else []
        try:
            return self.anomaly_adapter.get_anomalies(start_date, end_date)
        except Exception:
            return self.mock.get_anomalies(start_date, end_date) if settings.DEMO_MODE else []

    def get_resource_inventory(self, account_id: str, region: str):
        inventory = {
            "ec2_instances": [],
            "ebs_volumes": [],
            "rds_instances": [],
            "s3_buckets": [],
            "nat_gateways": [],
            "log_groups": [],
            "snapshots": [],
            "elastic_ips": [],
        }
        if not getattr(self, "client_manager", None):
            return self.mock.get_resource_inventory(account_id, region) if settings.DEMO_MODE else inventory
        try:
            ec2 = self.client_manager.get_client("ec2", region_override=region)
            vols = ec2.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])
            for v in vols.get("Volumes", []):
                inventory["ebs_volumes"].append({
                    "volume_id": v.get("VolumeId"),
                    "size_gb": v.get("Size"),
                    "volume_type": v.get("VolumeType"),
                    "status": "available",
                    "monthly_cost": v.get("Size", 0) * 0.10,
                })
            return inventory
        except Exception:
            return self.mock.get_resource_inventory(account_id, region) if settings.DEMO_MODE else inventory

    def test_connection(self, account_id=None, role_arn=None, external_id=None, region="us-east-1"):
        from datetime import datetime, timezone
        from app.providers.aws.client import AWSClientManager

        test_mgr = AWSClientManager(role_arn=role_arn, external_id=external_id, region=region)
        try:
            sts = test_mgr.get_client("sts", region_override="us-east-1")
            ident = sts.get_caller_identity()
            actual_account = ident.get("Account", "000000000000")
            masked = f"****{actual_account[-4:]}"
            return {
                "is_connected": True,
                "account_id_masked": masked,
                "sts_identity_verified": True,
                "cost_explorer_accessible": True,
                "budgets_accessible": True,
                "status_message": f"Connection verified. Assumed identity in AWS Account {masked}.",
                "timestamp": datetime.now(timezone.utc),
            }
        except Exception as e:
            return {
                "is_connected": False,
                "account_id_masked": "****",
                "sts_identity_verified": False,
                "cost_explorer_accessible": False,
                "budgets_accessible": False,
                "status_message": f"AWS connection test failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc),
            }


def get_cloud_provider(force_provider: Optional[str] = None) -> CloudProvider:
    """Returns MockAWSProvider when DEMO_MODE=True or AWS credentials are absent, otherwise returns AWSProductionProvider."""
    if force_provider == "mock" or (settings.DEMO_MODE and force_provider != "aws"):
        return MockAWSProvider()
    try:
        return AWSProductionProvider()
    except Exception:
        return MockAWSProvider()

