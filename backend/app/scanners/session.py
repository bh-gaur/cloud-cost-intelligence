"""
Scanner AWS Session Manager
Resolves authenticated boto3 sessions via STS AssumeRole per connected tenant AWS account.
"""

import boto3
from botocore.config import Config
from typing import Optional
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

BOTO3_CONFIG = Config(
    retries={"max_attempts": 5, "mode": "standard"},
    connect_timeout=5,
    read_timeout=15,
)


class AWSSessionManager:
    @staticmethod
    def get_session(
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        session_name: str = "CloudCostScannerSession",
    ) -> boto3.Session:
        """
        Returns a boto3 Session for scanning:
        - If role_arn is provided, assumes the cross-account role with the ExternalID.
        - Otherwise, returns a session using ambient/static credentials.
        """
        if not role_arn:
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                return boto3.Session(
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=settings.AWS_SESSION_TOKEN or None,
                    region_name=settings.AWS_DEFAULT_REGION,
                )
            return boto3.Session(region_name=settings.AWS_DEFAULT_REGION)

        try:
            sts_kwargs = {"config": BOTO3_CONFIG}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                sts_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                sts_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
                if settings.AWS_SESSION_TOKEN:
                    sts_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

            sts = boto3.client("sts", **sts_kwargs)
            assume_kwargs = {
                "RoleArn": role_arn,
                "RoleSessionName": session_name,
                "DurationSeconds": 3600,
            }
            if external_id:
                assume_kwargs["ExternalId"] = external_id

            response = sts.assume_role(**assume_kwargs)
            creds = response["Credentials"]

            return boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds["SessionToken"],
                region_name=settings.AWS_DEFAULT_REGION,
            )
        except Exception as e:
            logger.error("Failed to assume role %s for scanning: %s", role_arn, e)
            raise

    @staticmethod
    def get_client(session: boto3.Session, service: str, region: str = "us-east-1"):
        return session.client(service, region_name=region, config=BOTO3_CONFIG)
