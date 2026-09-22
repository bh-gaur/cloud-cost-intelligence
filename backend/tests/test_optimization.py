"""
Tests for Optimization Rules
"""

from decimal import Decimal
import pytest
from app.optimization.rules.ec2_idle import EC2IdleRule
from app.optimization.rules.ebs_unused import EBSUnusedRule
from app.optimization.rules.s3_storage import S3StorageRule
from app.optimization.rules.nat_gateway import NATGatewayRule
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


def test_optimization_engine_run(db_session):
    provider = MockAWSProvider()
    engine = OptimizationEngine(provider)
    recs = engine.run_all(db_session)
    assert len(recs) > 0

    summary = OptimizationEngine.get_summary(db_session)
    assert summary["total_monthly_savings"] > Decimal("0.00")
    assert summary["total_annual_savings"] > Decimal("0.00")

