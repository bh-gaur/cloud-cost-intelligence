"""
Tests for Optimization Rules
"""

from decimal import Decimal
import pytest
from app.optimization.rules.ec2_idle import EC2IdleRule
from app.optimization.rules.ebs_unused import EBSUnusedRule
from app.optimization.rules.elastic_ip import ElasticIPRule
from app.optimization.rules.s3_storage import S3StorageRule
from app.optimization.rules.snapshots import SnapshotAgeRule
from app.optimization.rules.tagging import TaggingComplianceRule
from app.optimization.engine import OptimizationEngine
from app.providers.mock.provider import MockAWSProvider


def test_ec2_idle_rule():
    rule = EC2IdleRule()
    inventory = {
        "ec2_instances": [
            {
                "instance_id": "i-idle-01",
                "instance_type": "m5.large",
                "state": "running",
                "average_cpu": 2.1,  # < 5%
                "monthly_cost": Decimal("140.00"),
            },
            {
                "instance_id": "i-busy-02",
                "instance_type": "m5.large",
                "state": "running",
                "average_cpu": 65.0,
                "monthly_cost": Decimal("140.00"),
            },
        ]
    }
    recs = rule.evaluate("123456789012", "us-east-1", inventory)
    assert len(recs) == 1
    assert recs[0].resource_id == "i-idle-01"
    assert recs[0].estimated_monthly_savings == Decimal("140.00")
    assert recs[0].confidence == "Observed"


def test_ebs_unused_rule():
    rule = EBSUnusedRule()
    inventory = {
        "ebs_volumes": [
            {
                "volume_id": "vol-available-1",
                "size_gb": 200,
                "status": "available",
                "monthly_cost": Decimal("20.00"),
            },
            {
                "volume_id": "vol-in-use-2",
                "size_gb": 100,
                "status": "in-use",
                "monthly_cost": Decimal("10.00"),
            },
        ]
    }
    recs = rule.evaluate("123456789012", "us-east-1", inventory)
    assert len(recs) == 1
    assert recs[0].resource_id == "vol-available-1"
    assert recs[0].estimated_monthly_savings == Decimal("20.00")


def test_elastic_ip_rule():
    rule = ElasticIPRule()
    inventory = {
        "elastic_ips": [
            {
                "public_ip": "54.210.12.34",
                "allocation_id": "eipalloc-112233",
                "association_id": None,
                "monthly_cost": Decimal("3.60"),
            },
            {
                "public_ip": "54.210.12.35",
                "allocation_id": "eipalloc-445566",
                "association_id": "eipassoc-778899",
                "monthly_cost": Decimal("0.00"),
            },
        ]
    }
    recs = rule.evaluate("123456789012", "us-east-1", inventory)
    assert len(recs) == 1
    assert recs[0].resource_id == "eipalloc-112233"
    assert recs[0].estimated_monthly_savings == Decimal("3.60")
    assert recs[0].confidence == "Observed"


def test_snapshots_rule():
    rule = SnapshotAgeRule()
    inventory = {
        "snapshots": [
            {
                "snapshot_id": "snap-old-01",
                "volume_size_gb": 500,
                "age_days": 120,
                "monthly_cost": Decimal("25.00"),
            },
            {
                "snapshot_id": "snap-fresh-02",
                "volume_size_gb": 100,
                "age_days": 15,
                "monthly_cost": Decimal("5.00"),
            },
        ]
    }
    recs = rule.evaluate("123456789012", "us-east-1", inventory)
    assert len(recs) == 1
    assert recs[0].resource_id == "snap-old-01"
    assert recs[0].estimated_monthly_savings == Decimal("25.00")


def test_tagging_rule():
    rule = TaggingComplianceRule()
    inventory = {
        "ec2_instances": [
            {
                "instance_id": "i-untagged",
                "tags": {},
                "monthly_cost": Decimal("50.00"),
            },
            {
                "instance_id": "i-tagged",
                "tags": {"Environment": "prod", "Team": "devops", "Application": "api"},
                "monthly_cost": Decimal("50.00"),
            },
        ]
    }
    recs = rule.evaluate("123456789012", "us-east-1", inventory)
    assert len(recs) == 1
    assert recs[0].resource_id == "i-untagged"


def test_optimization_engine_run(db_session):
    provider = MockAWSProvider()
    engine = OptimizationEngine(provider)
    recs = engine.run_all(db_session)
    assert len(recs) > 0

    summary = OptimizationEngine.get_summary(db_session)
    assert summary["total_monthly_savings"] > Decimal("0.00")
    assert summary["total_annual_savings"] > Decimal("0.00")

