"""
Cloud Provider Abstract Base Class
Defines the uniform interface for all cloud cost and telemetry providers.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional


class CloudProvider(ABC):
    """
    Abstract Cloud Provider Interface.
    Enables pluggable implementations for AWS, Mock (Demo Mode), Azure, and GCP.
    """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the identifier for this provider (e.g. 'aws', 'mock')."""
        pass

    @abstractmethod
    def fetch_cost_and_usage(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetches granular daily cost records grouped by service, account, region, and tags.
        """
        pass

    @abstractmethod
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Discovers linked cloud accounts."""
        pass

    @abstractmethod
    def get_budgets(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetches active cloud budget definitions and current utilization."""
        pass

    @abstractmethod
    def get_anomalies(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Fetches cloud-native anomaly detection records."""
        pass

    @abstractmethod
    def get_resource_inventory(
        self, account_id: str, region: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves live resource metadata needed for optimization rules
        (e.g., EC2 instances, EBS volumes, RDS instances, S3 buckets, NAT gateways, Log groups).
        """
        pass

    @abstractmethod
    def test_connection(
        self,
        account_id: Optional[str] = None,
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        region: str = "us-east-1",
    ) -> Dict[str, Any]:
        """Tests credentials and API accessibility."""
        pass

