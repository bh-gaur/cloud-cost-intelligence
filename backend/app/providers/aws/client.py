"""
AWS Boto3 Client Factory
Handles secure credential resolution via STS AssumeRole with External ID or ambient environment.
"""

import logging
from typing import Any, Optional
import boto3
from botocore.config import Config
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Standard retry and timeout configuration for AWS SDK calls
BOTO_CONFIG = Config(
    retries={"max_attempts": 3, "mode": "standard"},
    connect_timeout=5,
    read_timeout=15,
)


class AWSClientManager:
    """Manages boto3 sessions and client lifecycle."""

    def __init__(
        self,
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        region: str = "us-east-1",
    ):
        self.role_arn = role_arn
        self.external_id = external_id
        self.region = region or settings.AWS_DEFAULT_REGION
        self._session: Optional[boto3.Session] = None

    def get_session(self) -> boto3.Session:
        """Resolves authenticated boto3 session."""
        if self._session:
            return self._session

        # 1. Check if STS AssumeRole is specified
        if self.role_arn:
            try:
                base_session = boto3.Session()
                sts_client = base_session.client("sts", region_name=self.region, config=BOTO_CONFIG)
                assume_role_kwargs = {
                    "RoleArn": self.role_arn,
                    "RoleSessionName": "FinOpsCostIntelligenceSession",
                    "DurationSeconds": 3600,
                }
                if self.external_id:
                    assume_role_kwargs["ExternalId"] = self.external_id

                response = sts_client.assume_role(**assume_role_kwargs)
                creds = response["Credentials"]
                self._session = boto3.Session(
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"],
                    region_name=self.region,
                )
                return self._session
            except Exception as e:
                logger.error("Failed to assume AWS IAM role %s: %s", self.role_arn, e)
                raise

        # 2. Static explicit credentials from settings if provided
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self._session = boto3.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                aws_session_token=settings.AWS_SESSION_TOKEN,
                region_name=self.region,
            )
            return self._session

        # 3. Ambient instance profile / container role / ~/.aws
        self._session = boto3.Session(region_name=self.region)
        return self._session

    def get_client(self, service_name: str, region_override: Optional[str] = None) -> Any:
        """Creates a boto3 client for a given AWS service."""
        session = self.get_session()
        region = region_override or self.region
        return session.client(service_name, region_name=region, config=BOTO_CONFIG)

