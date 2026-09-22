"""
Tag Governance & Untagged Resource Explorer Schemas
"""

from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel


class TagPolicyRule(BaseModel):
    tag_key: str
    description: str
    is_required: bool = True
    allowed_values: Optional[List[str]] = None


class UntaggedResource(BaseModel):
    resource_id: str
    resource_name: str
    service: str
    resource_type: str
    region: str
    account_id: str
    missing_tags: List[str]
    existing_tags: Dict[str, str]
    monthly_spend: Decimal
    compliance_score: float  # 0 to 100
    cli_remediation: str
    terraform_remediation: str


class ServiceTagCompliance(BaseModel):
    service: str
    total_resources: int
    tagged_resources: int
    untagged_resources: int
    compliance_percentage: Decimal
    untagged_spend: Decimal


class TagGovernanceResponse(BaseModel):
    overall_compliance_percentage: Decimal
    total_spend: Decimal
    tagged_spend: Decimal
    untagged_spend: Decimal
    total_resources: int
    untagged_resources_count: int
    required_tags: List[str]
    service_breakdowns: List[ServiceTagCompliance]
    missing_by_tag_key: Dict[str, int]
    resources: List[UntaggedResource]


class RemediationGenerateRequest(BaseModel):
    resource_id: str
    service: str
    region: str
    resource_type: str
    custom_tags: Dict[str, str]


class RemediationGenerateResponse(BaseModel):
    resource_id: str
    cli_command: str
    terraform_snippet: str
