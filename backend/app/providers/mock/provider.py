"""
Mock AWS Provider for Demo Mode
Generates deterministic, production-grade simulated FinOps datasets for all AWS services,
accounts, regions, tags, anomalies, and resource states.
"""

import hashlib
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.providers.base import CloudProvider
from app.utils.money import to_decimal


class MockAWSProvider(CloudProvider):
    """
    Simulates comprehensive multi-account AWS environment with realistic spend patterns.
    """

    MOCK_ACCOUNTS = [
        {"account_id": "123456789012", "account_name": "Production Account", "status": "ACTIVE", "is_master": True},
        {"account_id": "987654321098", "account_name": "Staging & QA Account", "status": "ACTIVE", "is_master": False},
        {"account_id": "555666777888", "account_name": "Data Analytics & ML", "status": "ACTIVE", "is_master": False},
        {"account_id": "111222333444", "account_name": "Shared Services & Network", "status": "ACTIVE", "is_master": False},
    ]

    MOCK_REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]

    # Base daily costs per service to establish realistic proportions
    SERVICE_SPECS = [
        {"service": "Amazon Elastic Compute Cloud - Compute", "category": "Compute", "base_cost": 425.50, "unit": "Hrs"},
        {"service": "Amazon Relational Database Service", "category": "Database", "base_cost": 280.25, "unit": "Hrs"},
        {"service": "Amazon Simple Storage Service", "category": "Storage", "base_cost": 145.80, "unit": "GB-Mo"},
        {"service": "Amazon Elastic Kubernetes Service", "category": "Containers", "base_cost": 165.00, "unit": "Hrs"},
        {"service": "Amazon Virtual Private Cloud", "category": "Networking", "base_cost": 95.40, "unit": "GB"},
        {"service": "AWS Lambda", "category": "Serverless", "base_cost": 45.20, "unit": "Reqs"},
        {"service": "Amazon CloudWatch", "category": "Monitoring", "base_cost": 38.60, "unit": "GB"},
        {"service": "Amazon DynamoDB", "category": "Database", "base_cost": 52.10, "unit": "RCU/WCU"},
        {"service": "Elastic Load Balancing", "category": "Networking", "base_cost": 64.30, "unit": "LCU-Hrs"},
        {"service": "AWS Data Transfer", "category": "Networking", "base_cost": 82.50, "unit": "GB"},
        {"service": "Amazon OpenSearch Service", "category": "Analytics", "base_cost": 75.00, "unit": "Hrs"},
        {"service": "Amazon Elastic Block Store", "category": "Storage", "base_cost": 110.00, "unit": "GB-Mo"},
    ]

    ENVIRONMENTS = ["production", "staging", "development", "sandbox"]
    TEAMS = ["platform", "backend-core", "data-science", "frontend", "devops"]
    APPLICATIONS = ["api-gateway", "billing-worker", "analytics-pipeline", "customer-portal"]

    def get_provider_name(self) -> str:
        return "mock"

    def fetch_cost_and_usage(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generates deterministic daily line items for each service, account, and region.
        """
        records: List[Dict[str, Any]] = []
        curr_date = start_date

        target_accounts = (
            [acc for acc in self.MOCK_ACCOUNTS if acc["account_id"] == account_id]
            if account_id and account_id != "all"
            else self.MOCK_ACCOUNTS
        )

        target_regions = (
            [r for r in self.MOCK_REGIONS if r == region]
            if region and region != "all" and region != "global"
            else self.MOCK_REGIONS
        )

        while curr_date <= end_date:
            day_str = curr_date.strftime("%Y-%m-%d")
            day_index = curr_date.toordinal()

            # Weekday multiplier: higher spend on weekdays, lower on weekends
            is_weekend = curr_date.weekday() >= 5
            day_factor = 0.82 if is_weekend else 1.05

            for acc in target_accounts:
                acc_id = acc["account_id"]
                acc_weight = 0.50 if "Production" in acc["account_name"] else 0.20

                for spec in self.SERVICE_SPECS:
                    service_name = spec["service"]
                    base = spec["base_cost"]

                    # Distribute across regions deterministically
                    for reg_idx, reg in enumerate(target_regions):
                        reg_weight = 0.45 if reg == "us-east-1" else 0.20

                        # Pseudo-random deterministic noise based on hash
                        seed_str = f"{day_str}-{acc_id}-{service_name}-{reg}"
                        hash_val = int(hashlib.md5(seed_str.encode()).hexdigest()[:6], 16)
                        noise = ((hash_val % 100) - 50) / 400.0  # -12.5% to +12.5%

                        # Introduce realistic anomaly for EC2 on recent days
                        anomaly_boost = 1.0
                        if service_name.startswith("Amazon Elastic Compute") and curr_date.day % 14 == 0:
                            anomaly_boost = 1.35  # 35% spike

                        cost_val = base * acc_weight * reg_weight * day_factor * (1.0 + noise) * anomaly_boost
                        if cost_val < 0.05:
                            continue

                        cost_dec = to_decimal(cost_val)
                        usage_qty = to_decimal(cost_val * 4.2)

                        # Tagging distribution (simulate 85% tagged, 15% untagged)
                        is_tagged = (hash_val % 100) < 85
                        tags = {}
                        if is_tagged:
                            env = self.ENVIRONMENTS[hash_val % len(self.ENVIRONMENTS)]
                            team = self.TEAMS[(hash_val // 10) % len(self.TEAMS)]
                            app = self.APPLICATIONS[(hash_val // 20) % len(self.APPLICATIONS)]
                            tags = {
                                "Environment": env,
                                "Team": team,
                                "Application": app,
                                "Project": "Phoenix-Cloud",
                            }

                        records.append({
                            "provider": "mock",
                            "date": curr_date,
                            "account_id": acc_id,
                            "account_name": acc["account_name"],
                            "region": reg,
                            "service": service_name,
                            "service_category": spec["category"],
                            "resource_id": f"arn:aws:{service_name.lower()[:3]}:{reg}:{acc_id}:res-{hash_val % 1000}",
                            "usage_quantity": usage_qty,
                            "usage_unit": spec["unit"],
                            "cost": cost_dec,
                            "currency": "USD",
                            "tags": tags,
                            "idempotency_key": f"mock-{seed_str}",
                            "metadata": {"demo": True, "source": "MockAWSProvider"},
                        })

            curr_date += timedelta(days=1)

        return records

    def get_accounts(self) -> List[Dict[str, Any]]:
        return self.MOCK_ACCOUNTS

    def get_budgets(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        today = date.today()
        month_start = today.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)

        return [
            {
                "budget_name": "Corporate Total Cloud Spend",
                "account_id": "123456789012",
                "budget_limit": Decimal("45000.0000"),
                "current_spend": Decimal("38210.4500"),
                "forecasted_spend": Decimal("44100.0000"),
                "remaining_budget": Decimal("6789.5500"),
                "percentage_consumed": Decimal("84.91"),
                "status": "Warning",
                "currency": "USD",
                "period_start": month_start,
                "period_end": month_end,
            },
            {
                "budget_name": "Production Account Hard Limit",
                "account_id": "123456789012",
                "budget_limit": Decimal("25000.0000"),
                "current_spend": Decimal("18450.2000"),
                "forecasted_spend": Decimal("22300.0000"),
                "remaining_budget": Decimal("6549.8000"),
                "percentage_consumed": Decimal("73.80"),
                "status": "Healthy",
                "currency": "USD",
                "period_start": month_start,
                "period_end": month_end,
            },
            {
                "budget_name": "Staging Non-Prod Budget",
                "account_id": "987654321098",
                "budget_limit": Decimal("6000.0000"),
                "current_spend": Decimal("5890.1500"),
                "forecasted_spend": Decimal("6850.0000"),
                "remaining_budget": Decimal("109.8500"),
                "percentage_consumed": Decimal("98.17"),
                "status": "Critical",
                "currency": "USD",
                "period_start": month_start,
                "period_end": month_end,
            },
        ]

    def get_anomalies(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        yesterday = date.today() - timedelta(days=1)
        return [
            {
                "id": "anomaly-mock-001",
                "date": yesterday.strftime("%Y-%m-%d"),
                "service": "Amazon Elastic Compute Cloud - Compute",
                "account_id": "123456789012",
                "region": "us-east-1",
                "severity": "CRITICAL",
                "impact_cost": Decimal("480.5000"),
                "score": 92,
                "root_cause": "Unexpected scaling in Auto Scaling Group (asg-worker-phoenix)",
            },
            {
                "id": "anomaly-mock-002",
                "date": (yesterday - timedelta(days=3)).strftime("%Y-%m-%d"),
                "service": "Amazon Virtual Private Cloud",
                "account_id": "111222333444",
                "region": "us-east-1",
                "severity": "WARNING",
                "impact_cost": Decimal("142.2000"),
                "score": 78,
                "root_cause": "Cross-AZ NAT Gateway traffic volume spike",
            },
        ]

    def get_resource_inventory(
        self, account_id: str, region: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Provides simulated resource inventory for FinOps optimization rules."""
        return {
            "ec2_instances": [
                {
                    "instance_id": "i-0a8b9c1d2e3f4001",
                    "instance_type": "m5.2xlarge",
                    "state": "running",
                    "average_cpu": 2.4,  # Under 5% idle
                    "peak_cpu": 4.1,
                    "tags": {"Environment": "staging", "Name": "legacy-analytics-worker"},
                    "monthly_cost": Decimal("280.32"),
                },
                {
                    "instance_id": "i-0a8b9c1d2e3f4002",
                    "instance_type": "c5.4xlarge",
                    "state": "running",
                    "average_cpu": 12.0,
                    "peak_cpu": 22.5,  # Oversized
                    "tags": {"Environment": "production", "Name": "api-indexer"},
                    "monthly_cost": Decimal("496.40"),
                },
                {
                    "instance_id": "i-0a8b9c1d2e3f4003",
                    "instance_type": "t3.medium",
                    "state": "running",
                    "average_cpu": 1.2,
                    "peak_cpu": 3.0,
                    "tags": {},  # Untagged
                    "monthly_cost": Decimal("30.36"),
                },
            ],
            "ebs_volumes": [
                {
                    "volume_id": "vol-0123456789abcdef0",
                    "size_gb": 500,
                    "volume_type": "gp2",
                    "status": "available",  # Unattached!
                    "monthly_cost": Decimal("50.00"),
                },
                {
                    "volume_id": "vol-0123456789abcdef1",
                    "size_gb": 1000,
                    "volume_type": "gp2",
                    "status": "available",  # Unattached!
                    "monthly_cost": Decimal("100.00"),
                },
            ],
            "rds_instances": [
                {
                    "db_instance_id": "rds-staging-postgres-01",
                    "instance_class": "db.r5.xlarge",
                    "engine": "postgres",
                    "multi_az": True,
                    "average_cpu": 4.8,  # Oversized
                    "max_connections": 8,
                    "monthly_cost": Decimal("360.00"),
                }
            ],
            "s3_buckets": [
                {
                    "bucket_name": "corp-analytics-archive-2024",
                    "size_gb": 45000,
                    "storage_class": "STANDARD",
                    "lifecycle_enabled": False,
                    "monthly_cost": Decimal("1035.00"),
                }
            ],
            "nat_gateways": [
                {
                    "nat_gateway_id": "nat-0987654321fedcba0",
                    "vpc_id": "vpc-01234567",
                    "state": "available",
                    "bytes_processed_daily_gb": 0.4,  # Idle NAT Gateway
                    "monthly_cost": Decimal("32.40"),
                }
            ],
            "log_groups": [
                {
                    "log_group_name": "/aws/containerinsights/phoenix/application",
                    "stored_bytes": 142000000000,  # ~142 GB
                    "retention_in_days": None,  # Never expire
                    "monthly_cost": Decimal("71.00"),
                }
            ],
            "snapshots": [
                {
                    "snapshot_id": "snap-0456789abcdef1234",
                    "volume_size_gb": 800,
                    "age_days": 185,
                    "monthly_cost": Decimal("40.00"),
                }
            ],
            "elastic_ips": [
                {
                    "public_ip": "54.210.12.34",
                    "association_id": None,  # Unattached EIP
                    "monthly_cost": Decimal("3.60"),
                }
            ],
        }

    def test_connection(
        self,
        account_id: Optional[str] = None,
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        region: str = "us-east-1",
    ) -> Dict[str, Any]:
        """Always succeeds in Mock / Demo mode."""
        acc_id = account_id or "123456789012"
        masked_id = f"****{acc_id[-4:]}"
        return {
            "is_connected": True,
            "account_id_masked": masked_id,
            "sts_identity_verified": True,
            "cost_explorer_accessible": True,
            "budgets_accessible": True,
            "status_message": f"Demo connection successful for AWS Account {masked_id} (Demo Provider)",
            "timestamp": datetime.now(timezone.utc),
        }

