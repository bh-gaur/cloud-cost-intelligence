"""
AWS Account Discovery & Identity Adapter
Resolves account identity via STS and lists accounts via AWS Organizations when permitted.
"""

import logging
from typing import Any, Dict, List
from botocore.exceptions import ClientError
from app.providers.aws.client import AWSClientManager

logger = logging.getLogger(__name__)


class AWSAccountAdapter:
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager

    def get_caller_identity(self) -> Dict[str, str]:
        """Resolves current STS caller identity."""
        sts = self.client_manager.get_client("sts", region_override="us-east-1")
        identity = sts.get_caller_identity()
        return {
            "account_id": identity.get("Account", "Unknown"),
            "arn": identity.get("Arn", ""),
            "user_id": identity.get("UserId", ""),
        }

    def list_organization_accounts(self) -> List[Dict[str, Any]]:
        """Discovers linked accounts if AWS Organizations API is enabled and authorized."""
        accounts = []
        try:
            org = self.client_manager.get_client("organizations", region_override="us-east-1")
            paginator = org.get_paginator("list_accounts")
            for page in paginator.paginate():
                for acc in page.get("Accounts", []):
                    accounts.append({
                        "account_id": acc.get("Id"),
                        "account_name": acc.get("Name", f"Account {acc.get('Id')}"),
                        "status": acc.get("Status"),
                        "is_master": acc.get("Id") == self.get_caller_identity()["account_id"],
                    })
        except ClientError as e:
            logger.warning("Organizations list_accounts not available: %s", e)
            # Fallback to current caller identity
            ident = self.get_caller_identity()
            accounts.append({
                "account_id": ident["account_id"],
                "account_name": f"Production Account ({ident['account_id'][-4:]})",
                "status": "ACTIVE",
                "is_master": True,
            })
        return accounts

