"""
Tests for Tag Governance & Untagged Resource Explorer
"""

import pytest
from decimal import Decimal
from app.services.tagging_service import TaggingService
from app.models.cost import CostRecord
from app.models.organization import Organization
from datetime import date


def test_tagging_service_remediation_generation():
    service = TaggingService()
    
    # Test S3 remediation command
    s3_cmd = service.generate_cli_remediation(
        service="Amazon S3",
        resource_id="prod-data-lake-raw",
        region="us-east-1",
        tags={"Environment": "production", "Owner": "data-team"},
    )
    assert "aws s3api put-bucket-tagging" in s3_cmd
    assert "prod-data-lake-raw" in s3_cmd

    # Test EC2 remediation command
    ec2_cmd = service.generate_cli_remediation(
        service="Amazon EC2",
        resource_id="i-0abc1234def567890",
        region="us-east-1",
        tags={"Environment": "production"},
    )
    assert "aws ec2 create-tags" in ec2_cmd
    assert "i-0abc1234def567890" in ec2_cmd

    # Test Terraform snippet
    tf = service.generate_terraform_remediation("compute", "i-123", {"Environment": "prod"})
    assert '"Environment" = "prod"' in tf


def test_tagging_governance_summary(db_session):
    # Setup test organization and cost record
    org = Organization(name="Tag Test Org", slug="tag-test-org", status="ACTIVE")
    db_session.add(org)
    db_session.flush()

    # Add untagged cost record
    r1 = CostRecord(
        organization_id=org.id,
        date=date.today(),
        account_id="123456789012",
        account_name="Production",
        service="Amazon S3",
        resource_id="untagged-bucket",
        cost=Decimal("12.5000"),
        tags={},
        idempotency_key=f"{org.id}-s3-untagged",
    )
    # Add tagged cost record
    r2 = CostRecord(
        organization_id=org.id,
        date=date.today(),
        account_id="123456789012",
        account_name="Production",
        service="Amazon EC2",
        resource_id="tagged-instance",
        cost=Decimal("25.0000"),
        tags={"Environment": "production", "Owner": "infra", "Project": "cloud", "Team": "devops"},
        idempotency_key=f"{org.id}-ec2-tagged",
    )
    db_session.add(r1)
    db_session.add(r2)
    db_session.commit()

    service = TaggingService()
    summary = service.get_governance_summary(db=db_session, organization_id=org.id)

    assert summary.total_resources >= 2
    assert summary.untagged_resources_count >= 1
    assert any(res.resource_id == "untagged-bucket" for res in summary.resources)
    assert summary.tagged_spend == Decimal("25.00")
    assert summary.untagged_spend >= Decimal("12.50")
