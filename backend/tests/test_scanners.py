"""
Unit and Integration Tests for AWS Deep Scanners & Optimization Engine
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from app.scanners.base import ScanContext, ScanFinding
from app.scanners.aws.ec2_scanner import EC2Scanner
from app.scanners.aws.rds_scanner import RDSScanner
from app.scanners.aws.s3_scanner import S3Scanner
from app.scanners.aws.networking_scanner import NetworkingScanner
from app.models.optimization import OptimizationRecommendation
from app.optimization.engine import OptimizationEngine
from app.providers.mock.provider import MockAWSProvider


def test_scan_finding_properties():
    finding = ScanFinding(
        rule_id="AWS-EC2-001",
        title="Idle EC2 Instance",
        description="Instance average CPU is 1.2% over 7 days",
        severity="HIGH",
        category="IDLE_RESOURCE",
        resource_type="EC2Instance",
        resource_id="i-0123456789abcdef0",
        resource_name="dev-web-server",
        region="us-east-1",
        estimated_monthly_savings=70.00,
        current_monthly_cost=70.00,
        implementation_effort="low",
        operational_risk="low",
        production_safety_score=95,
        confidence="Observed",
        remediation_steps="Stop or terminate instance",
        remediation_code="aws ec2 stop-instances --instance-ids i-0123456789abcdef0 --region us-east-1",
    )

    assert finding.rule_id == "AWS-EC2-001"
    assert finding.fingerprint() is not None
    d = finding.to_dict()
    assert d["rule_id"] == "AWS-EC2-001"
    assert d["production_safety_score"] == 95


def test_ec2_scanner_idle_and_unattached():
    mock_session = MagicMock()
    mock_ec2 = MagicMock()
    mock_cw = MagicMock()

    # Mock EC2 paginators
    ec2_paginator_inst = MagicMock()
    ec2_paginator_inst.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-idle-01",
                            "InstanceType": "t3.medium",
                            "State": {"Name": "running"},
                            "LaunchTime": datetime.now(timezone.utc) - timedelta(days=10),
                            "Tags": [{"Key": "Name", "Value": "staging-idle"}],
                        },
                        {
                            "InstanceId": "i-stopped-02",
                            "InstanceType": "m5.large",
                            "State": {"Name": "stopped"},
                            "LaunchTime": datetime.now(timezone.utc) - timedelta(days=20),
                            "Tags": [],
                        }
                    ]
                }
            ]
        }
    ]

    ec2_paginator_vol = MagicMock()
    ec2_paginator_vol.paginate.side_effect = [
        # Available volumes
        [
            {
                "Volumes": [
                    {
                        "VolumeId": "vol-orphan-1",
                        "Size": 100,
                        "VolumeType": "gp3",
                        "State": "available",
                        "Tags": [],
                    }
                ]
            }
        ],
        # gp2 volumes
        [
            {
                "Volumes": [
                    {
                        "VolumeId": "vol-attached-gp2",
                        "Size": 500,
                        "VolumeType": "gp2",
                        "State": "in-use",
                        "Tags": [],
                    }
                ]
            }
        ]
    ]

    def paginator_side_effect(operation_name):
        if operation_name == "describe_instances":
            return ec2_paginator_inst
        if operation_name == "describe_volumes":
            return ec2_paginator_vol
        return MagicMock()

    mock_ec2.get_paginator.side_effect = paginator_side_effect

    # CloudWatch metrics for idle check
    mock_cw.get_metric_data.return_value = {
        "MetricDataResults": [
            {"Values": [1.5, 2.0, 1.8]}
        ]
    }

    # Unattached EIPs
    mock_ec2.describe_addresses.return_value = {
        "Addresses": [
            {
                "PublicIp": "54.210.10.20",
                "AllocationId": "eipalloc-12345",
            }
        ]
    }

    ctx = ScanContext(
        organization_id="org-test-123",
        aws_account_id="123456789012",
        aws_account_name="Production",
        regions=["us-east-1"],
    )

    with patch("app.scanners.aws.ec2_scanner.AWSSessionManager") as mock_mgr:
        mock_mgr.get_session.return_value = mock_session
        mock_mgr.get_client.side_effect = lambda sess, service, region: mock_ec2 if service == "ec2" else mock_cw
        scanner = EC2Scanner(ctx)
        findings = scanner.scan()

    rule_ids = [f.rule_id for f in findings]
    assert "EC2-IDLE" in rule_ids
    assert "EC2-STOPPED" in rule_ids
    assert "EBS-UNUSED" in rule_ids
    assert "EBS-GP2-TO-GP3" in rule_ids
    assert "EIP-UNATTACHED" in rule_ids


def test_rds_scanner_idle_and_snapshots():
    mock_session = MagicMock()
    mock_rds = MagicMock()
    mock_cw = MagicMock()

    rds_paginator_inst = MagicMock()
    rds_paginator_inst.paginate.return_value = [
        {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "dev-postgres-db",
                    "DBInstanceClass": "db.t3.medium",
                    "Engine": "postgres",
                    "DBInstanceStatus": "available",
                    "MultiAZ": True,  # Non-prod multi-az waste
                    "AllocatedStorage": 100,
                    "StorageType": "gp2",  # gp2 to gp3 waste
                    "TagList": [{"Key": "Environment", "Value": "development"}],
                }
            ]
        }
    ]

    # Stale manual snapshot (> 90 days)
    rds_paginator_snap = MagicMock()
    rds_paginator_snap.paginate.return_value = [
        {
            "DBSnapshots": [
                {
                    "DBSnapshotIdentifier": "rds:dev-postgres-db-manual-backup",
                    "DBInstanceIdentifier": "dev-postgres-db",
                    "SnapshotType": "manual",
                    "AllocatedStorage": 100,
                    "SnapshotCreateTime": datetime.now(timezone.utc) - timedelta(days=120),
                }
            ]
        }
    ]

    def rds_paginator_side_effect(op):
        if op == "describe_db_instances":
            return rds_paginator_inst
        if op == "describe_db_snapshots":
            return rds_paginator_snap
        return MagicMock()

    mock_rds.get_paginator.side_effect = rds_paginator_side_effect

    # CloudWatch: zero connections
    mock_cw.get_metric_data.return_value = {
        "MetricDataResults": [
            {"Values": [0.0, 0.0, 0.0]}
        ]
    }

    ctx = ScanContext(
        organization_id="org-test-123",
        aws_account_id="123456789012",
        aws_account_name="Production",
        regions=["us-east-1"],
    )

    with patch("app.scanners.aws.rds_scanner.AWSSessionManager") as mock_mgr:
        mock_mgr.get_session.return_value = mock_session
        mock_mgr.get_client.side_effect = lambda sess, service, region: mock_rds if service == "rds" else mock_cw
        scanner = RDSScanner(ctx)
        findings = scanner.scan()

    rule_ids = [f.rule_id for f in findings]
    assert "RDS-IDLE" in rule_ids
    assert "RDS-MULTIAZ-NONPROD" in rule_ids
    assert "RDS-STORAGE-GP3" in rule_ids
    assert "RDS-OLD-SNAPSHOT" in rule_ids


def test_s3_scanner_lifecycle_and_multipart():
    mock_session = MagicMock()
    mock_s3 = MagicMock()

    mock_s3.list_buckets.return_value = {
        "Buckets": [
            {"Name": "test-data-bucket-no-lifecycle", "CreationDate": datetime.now(timezone.utc) - timedelta(days=90)},
        ]
    }

    mock_s3.get_bucket_location.return_value = {"LocationConstraint": "us-east-1"}

    from botocore.exceptions import ClientError
    error_response = {"Error": {"Code": "NoSuchLifecycleConfiguration", "Message": "The lifecycle configuration does not exist"}}
    mock_s3.get_bucket_lifecycle_configuration.side_effect = ClientError(error_response, "GetBucketLifecycleConfiguration")

    mock_s3.list_multipart_uploads.return_value = {
        "Uploads": [
            {
                "UploadId": "upload-xyz-123",
                "Key": "big-dataset.tar.gz",
                "Initiated": datetime.now(timezone.utc) - timedelta(days=15),
            }
        ]
    }

    ctx = ScanContext(
        organization_id="org-test-123",
        aws_account_id="123456789012",
        aws_account_name="Production",
        regions=["us-east-1"],
    )

    with patch("app.scanners.aws.s3_scanner.AWSSessionManager") as mock_mgr:
        mock_mgr.get_session.return_value = mock_session
        mock_mgr.get_client.return_value = mock_s3
        scanner = S3Scanner(ctx)
        findings = scanner.scan()

    rule_ids = [f.rule_id for f in findings]
    assert "S3-LIFECYCLE-MISSING" in rule_ids
    assert "S3-MULTIPART-INCOMPLETE" in rule_ids


def test_networking_scanner_nat_and_alb():
    mock_session = MagicMock()
    mock_ec2 = MagicMock()
    mock_elbv2 = MagicMock()
    mock_cw = MagicMock()

    # NAT Gateway Paginator
    nat_paginator = MagicMock()
    nat_paginator.paginate.return_value = [
        {
            "NatGateways": [
                {
                    "NatGatewayId": "nat-0123456789abcdef0",
                    "VpcId": "vpc-01234",
                    "State": "available",
                    "CreateTime": datetime.now(timezone.utc) - timedelta(days=14),
                    "Tags": [{"Key": "Name", "Value": "idle-nat-gateway"}],
                }
            ]
        }
    ]
    mock_ec2.get_paginator.return_value = nat_paginator

    # ELBv2 Paginator
    elb_paginator = MagicMock()
    elb_paginator.paginate.return_value = [
        {
            "LoadBalancers": [
                {
                    "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/idle-alb/50dc6c495c0c9188",
                    "LoadBalancerName": "idle-alb",
                    "Type": "application",
                    "State": {"Code": "active"},
                    "CreatedTime": datetime.now(timezone.utc) - timedelta(days=14),
                }
            ]
        }
    ]
    mock_elbv2.get_paginator.return_value = elb_paginator
    mock_elbv2.describe_target_groups.return_value = {"TargetGroups": []}

    mock_cw.get_metric_data.return_value = {
        "MetricDataResults": [
            {"Values": [0.0, 0.0, 0.0]}  # 0 bytes traffic, 0 requests
        ]
    }

    ctx = ScanContext(
        organization_id="org-test-123",
        aws_account_id="123456789012",
        aws_account_name="Production",
        regions=["us-east-1"],
    )

    with patch("app.scanners.aws.networking_scanner.AWSSessionManager") as mock_mgr:
        mock_mgr.get_session.return_value = mock_session
        def client_side_effect(sess, service, region):
            if service == "ec2":
                return mock_ec2
            if service == "elbv2":
                return mock_elbv2
            if service == "cloudwatch":
                return mock_cw
            return MagicMock()

        mock_mgr.get_client.side_effect = client_side_effect
        scanner = NetworkingScanner(ctx)
        findings = scanner.scan()

    rule_ids = [f.rule_id for f in findings]
    assert "NET-IDLE-NAT" in rule_ids
    assert "NET-UNUSED-ALB" in rule_ids



def test_optimization_engine_with_mock_provider(db_session):
    provider = MockAWSProvider()
    engine = OptimizationEngine(provider)
    recs = engine.run_all(db_session, organization_id="org-test-engine")
    assert len(recs) > 0

    # Ensure all recommendations have organization_id
    for r in recs:
        assert r.organization_id == "org-test-engine"

    summary = OptimizationEngine.get_summary(db_session, organization_id="org-test-engine")
    assert summary["total_monthly_savings"] > Decimal("0.00")
    assert summary["total_recommendations"] == len(recs)
