"""
AWS Resource Tagging Adapter
Analyzes tagging coverage using Cost Explorer tag dimensions and Resource Tagging API.
"""

import logging
from typing import Any, Dict, List
from botocore.exceptions import ClientError
from app.providers.aws.client import AWSClientManager

logger = logging.getLogger(__name__)


class AWSTaggingAdapter:
    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager

    def get_tag_keys(self) -> List[str]:
        """Retrieves active cost allocation tag keys from Cost Explorer."""
        try:
            ce = self.client_manager.get_client("ce", region_override="us-east-1")
            response = ce.get_tags(TimePeriod={"Start": "2026-01-01", "End": "2026-12-31"})
            return response.get("Tags", [])
        except ClientError as e:
            logger.warning("Error fetching tag keys: %s", e)
            return ["Environment", "Team", "Application", "Project", "Owner"]

