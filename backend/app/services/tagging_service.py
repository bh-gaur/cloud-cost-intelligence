"""
FinOps Tag Governance & Untagged Resource Discovery Service
Evaluates multi-cloud tag policies, identifies untagged infrastructure, and generates automated remediation code.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.cost import CostRecord
from app.models.optimization import OptimizationRecommendation
from app.models.account import AWSAccount
from app.schemas.tagging import (
    TagGovernanceResponse,
    ServiceTagCompliance,
    UntaggedResource,
    RemediationGenerateResponse,
)

DEFAULT_REQUIRED_TAGS = ["Environment", "Owner", "Project", "Team"]


class TaggingService:
    def __init__(self, required_tags: Optional[List[str]] = None):
        self.required_tags = required_tags or DEFAULT_REQUIRED_TAGS

    @staticmethod
    def generate_cli_remediation(service: str, resource_id: str, region: str, tags: Dict[str, str]) -> str:
        """Generates the appropriate AWS CLI command to attach tags."""
        svc_lower = (service or "").lower()
        tag_args = " ".join([f"Key={k},Value={v}" for k, v in tags.items()])

        if "s3" in svc_lower or "bucket" in svc_lower:
            tag_set = ",".join([f"{{Key={k},Value={v}}}" for k, v in tags.items()])
            return f"aws s3api put-bucket-tagging --bucket {resource_id} --tagging 'TagSet=[{tag_set}]' --region {region}"
        elif "rds" in svc_lower or "database" in svc_lower:
            tags_json = " ".join([f"Key={k},Value={v}" for k, v in tags.items()])
            return f"aws rds add-tags-to-resource --resource-name {resource_id} --tags {tags_json} --region {region}"
        elif "lambda" in svc_lower:
            tags_str = ",".join([f"{k}={v}" for k, v in tags.items()])
            return f"aws lambda tag-resource --resource {resource_id} --tags {tags_str} --region {region}"
        else:
            # Default EC2 / EBS / VPC resource tagging
            return f"aws ec2 create-tags --resources {resource_id} --tags {tag_args} --region {region}"

    @staticmethod
    def generate_terraform_remediation(resource_type: str, resource_id: str, tags: Dict[str, str]) -> str:
        """Generates Terraform HCL tags block."""
        lines = ["  tags = {"]
        for k, v in tags.items():
            lines.append(f'    "{k}" = "{v}"')
        lines.append("  }")
        tags_block = "\n".join(lines)
        return f"# Add to resource block in Terraform:\n{tags_block}"

    def get_governance_summary(
        self,
        db: Session,
        organization_id: Optional[str] = None,
        account_id: str = "all",
    ) -> TagGovernanceResponse:
        """
        Analyzes cost records and optimization recommendations to build a comprehensive
        Tag Governance scorecard and list of untagged resources.
        """
        # 1. Total Spend and Tagged Spend Analysis
        cost_q = db.query(CostRecord)
        if organization_id:
            cost_q = cost_q.filter(CostRecord.organization_id == organization_id)
        if account_id != "all":
            cost_q = cost_q.filter(CostRecord.account_id == account_id)

        all_cost_records = cost_q.all()

        total_spend = Decimal("0.0000")
        tagged_spend = Decimal("0.0000")

        # Map by unique resource_id
        resources_map: Dict[str, Dict[str, Any]] = {}

        for rec in all_cost_records:
            total_spend += rec.cost
            rec_tags = rec.tags or {}
            if rec_tags:
                tagged_spend += rec.cost

            # Aggregate resources
            res_id = rec.resource_id or f"{rec.service}-{rec.account_id}-{rec.region}"
            if res_id not in resources_map:
                resources_map[res_id] = {
                    "resource_id": res_id,
                    "resource_name": rec.resource_id or rec.service,
                    "service": rec.service,
                    "resource_type": rec.service_category or "infrastructure",
                    "region": rec.region,
                    "account_id": rec.account_id,
                    "existing_tags": dict(rec_tags),
                    "spend": Decimal("0.0000"),
                }
            resources_map[res_id]["spend"] += rec.cost
            # Merge existing tags if any
            resources_map[res_id]["existing_tags"].update(rec_tags)

        # 2. Also incorporate Optimization recommendations for discovered cloud resources
        opt_q = db.query(OptimizationRecommendation)
        if organization_id:
            opt_q = opt_q.filter(OptimizationRecommendation.organization_id == organization_id)
        if account_id != "all":
            opt_q = opt_q.filter(OptimizationRecommendation.account_id == account_id)

        for opt in opt_q.all():
            r_id = opt.resource_id or opt.resource_name
            if r_id and r_id not in resources_map:
                resources_map[r_id] = {
                    "resource_id": r_id,
                    "resource_name": opt.resource_name or r_id,
                    "service": opt.service,
                    "resource_type": getattr(opt, "service", None) or "compute",
                    "region": opt.region or "us-east-1",
                    "account_id": opt.account_id,
                    "existing_tags": {},
                    "spend": opt.estimated_monthly_savings or Decimal("5.00"),
                }

        # 3. Analyze compliance per resource
        untagged_list: List[UntaggedResource] = []
        service_stats: Dict[str, Dict[str, Any]] = {}
        missing_by_key: Dict[str, int] = {k: 0 for k in self.required_tags}

        for r_id, r in resources_map.items():
            svc = r["service"]
            if svc not in service_stats:
                service_stats[svc] = {
                    "total": 0,
                    "tagged": 0,
                    "untagged": 0,
                    "untagged_spend": Decimal("0.0000"),
                }

            service_stats[svc]["total"] += 1

            existing_tags = r["existing_tags"]
            missing_tags = [req_k for req_k in self.required_tags if req_k not in existing_tags]

            for m in missing_tags:
                missing_by_key[m] = missing_by_key.get(m, 0) + 1

            compliance_pct = ((len(self.required_tags) - len(missing_tags)) / len(self.required_tags)) * 100.0

            # Generate default remediation tags
            default_tags = {k: f"default-{k.lower()}" for k in missing_tags}
            if "Environment" in default_tags:
                default_tags["Environment"] = "production"
            if "Owner" in default_tags:
                default_tags["Owner"] = "finops-team"

            cli_cmd = self.generate_cli_remediation(svc, r["resource_id"], r["region"], default_tags)
            tf_code = self.generate_terraform_remediation(r["resource_type"], r["resource_id"], default_tags)

            monthly_spend = r["spend"]

            if missing_tags:
                service_stats[svc]["untagged"] += 1
                service_stats[svc]["untagged_spend"] += monthly_spend
                untagged_list.append(
                    UntaggedResource(
                        resource_id=r["resource_id"],
                        resource_name=r["resource_name"],
                        service=svc,
                        resource_type=r["resource_type"],
                        region=r["region"],
                        account_id=r["account_id"],
                        missing_tags=missing_tags,
                        existing_tags=existing_tags,
                        monthly_spend=monthly_spend.quantize(Decimal("0.01")),
                        compliance_score=round(compliance_pct, 1),
                        cli_remediation=cli_cmd,
                        terraform_remediation=tf_code,
                    )
                )
            else:
                service_stats[svc]["tagged"] += 1

        # 4. Service Breakdown List
        service_breakdowns: List[ServiceTagCompliance] = []
        for svc, s in service_stats.items():
            tot = s["total"]
            tagged = s["tagged"]
            pct = Decimal("100.00") if tot == 0 else (Decimal(str(tagged)) / Decimal(str(tot)) * Decimal("100.00")).quantize(Decimal("0.01"))
            service_breakdowns.append(
                ServiceTagCompliance(
                    service=svc,
                    total_resources=tot,
                    tagged_resources=tagged,
                    untagged_resources=s["untagged"],
                    compliance_percentage=pct,
                    untagged_spend=s["untagged_spend"].quantize(Decimal("0.01")),
                )
            )

        service_breakdowns.sort(key=lambda x: x.untagged_spend, reverse=True)

        # 5. Overall Metrics
        total_res_count = len(resources_map)
        untagged_count = len(untagged_list)
        tagged_count = total_res_count - untagged_count
        overall_pct = (
            Decimal("100.00")
            if total_res_count == 0
            else (Decimal(str(tagged_count)) / Decimal(str(total_res_count)) * Decimal("100.00")).quantize(Decimal("0.01"))
        )
        untagged_spend = max(Decimal("0.0000"), total_spend - tagged_spend).quantize(Decimal("0.01"))

        # Sort untagged resources by monthly spend descending
        untagged_list.sort(key=lambda x: x.monthly_spend, reverse=True)

        return TagGovernanceResponse(
            overall_compliance_percentage=overall_pct,
            total_spend=total_spend.quantize(Decimal("0.01")),
            tagged_spend=tagged_spend.quantize(Decimal("0.01")),
            untagged_spend=untagged_spend,
            total_resources=total_res_count,
            untagged_resources_count=untagged_count,
            required_tags=self.required_tags,
            service_breakdowns=service_breakdowns,
            missing_by_tag_key=missing_by_key,
            resources=untagged_list,
        )
