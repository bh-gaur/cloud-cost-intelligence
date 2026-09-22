"""
Optimization Engine Orchestrator
Executes deep AWS resource scanners (EC2, EBS, RDS, S3, Networking) via STS AssumeRole
and synchronizes actionable recommendations with remediation CLI snippets.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.optimization import OptimizationRecommendation
from app.models.account import AWSAccount
from app.optimization.rules.base import BaseOptimizationRule, Recommendation
from app.optimization.rules.ec2_idle import EC2IdleRule
from app.optimization.rules.ec2_rightsizing import EC2RightsizingRule
from app.optimization.rules.ebs_unused import EBSUnusedRule
from app.optimization.rules.rds_rightsizing import RDSRightsizingRule
from app.optimization.rules.s3_storage import S3StorageRule
from app.optimization.rules.nat_gateway import NATGatewayRule
from app.optimization.rules.cloudwatch import CloudWatchRetentionRule
from app.optimization.rules.snapshots import SnapshotAgeRule
from app.optimization.rules.tagging import TaggingComplianceRule
from app.optimization.rules.savings_plans import SavingsPlansRule
from app.optimization.rules.reserved_instances import ReservedInstancesRule
from app.providers.base import CloudProvider
from app.scanners.base import ScanContext, ScanFinding
from app.scanners.aws.ec2_scanner import EC2Scanner
from app.scanners.aws.rds_scanner import RDSScanner
from app.scanners.aws.s3_scanner import S3Scanner
from app.scanners.aws.networking_scanner import NetworkingScanner

logger = logging.getLogger(__name__)


class OptimizationEngine:
    def __init__(self, provider: CloudProvider):
        self.provider = provider
        self.rules: List[BaseOptimizationRule] = [
            EC2IdleRule(),
            EC2RightsizingRule(),
            EBSUnusedRule(),
            RDSRightsizingRule(),
            S3StorageRule(),
            NATGatewayRule(),
            CloudWatchRetentionRule(),
            SnapshotAgeRule(),
            TaggingComplianceRule(),
            SavingsPlansRule(),
            ReservedInstancesRule(),
        ]

    def run_all(
        self,
        db: Session,
        account_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> List[OptimizationRecommendation]:
        """Evaluates all rules & live resource scanners across connected accounts and saves recommendations."""
        if not organization_id:
            from app.models.organization import Organization
            default_org = db.query(Organization).filter(Organization.slug == "default-org").first()
            if not default_org:
                default_org = Organization(name="Default Organization", slug="default-org", status="ACTIVE")
                db.add(default_org)
                db.flush()
            organization_id = default_org.id

        persisted_records: List[OptimizationRecommendation] = []

        # 1. If live connected AWS accounts exist and not in DEMO_MODE, run deep live scanners
        db_accounts = []
        if not settings.DEMO_MODE:
            q = db.query(AWSAccount).filter(AWSAccount.organization_id == organization_id)
            if account_id and account_id != "all":
                q = q.filter(AWSAccount.account_id == account_id)
            db_accounts = q.all()

        if db_accounts:
            for acc in db_accounts:
                try:
                    context = ScanContext(
                        organization_id=organization_id,
                        aws_account_id=acc.account_id,
                        aws_account_name=acc.account_name,
                        role_arn=acc.role_arn,
                        external_id=acc.external_id,
                        regions=[acc.default_region or "us-east-1"],
                    )

                    scanners = [
                        EC2Scanner(context),
                        RDSScanner(context),
                        S3Scanner(context),
                        NetworkingScanner(context),
                    ]

                    for scanner in scanners:
                        try:
                            findings = scanner.scan()
                            for f in findings:
                                rec = self._upsert_finding(db, organization_id, acc.account_id, f)
                                persisted_records.append(rec)
                        except Exception as e:
                            logger.error("Error executing scanner %s on account %s: %s", scanner.__class__.__name__, acc.account_id, e)
                except Exception as e:
                    logger.warning("Could not execute live AWS scanners for account %s (%s): %s", acc.account_id, acc.account_name, e)

        # 2. In DEMO_MODE or when no live scanner findings were persisted, evaluate mock inventory rules
        if settings.DEMO_MODE or not persisted_records:
            accounts = self.provider.get_accounts()
            if account_id and account_id != "all":
                accounts = [a for a in accounts if a["account_id"] == account_id]

            for acc in accounts:
                acc_id = acc["account_id"]
                inventory = self.provider.get_resource_inventory(acc_id, region="us-east-1")

                for rule in self.rules:
                    try:
                        recs = rule.evaluate(acc_id, region="us-east-1", inventory=inventory)
                        for r in recs:
                            persisted = self._upsert_rule_recommendation(db, organization_id, r)
                            persisted_records.append(persisted)
                    except Exception as e:
                        logger.error("Error evaluating rule %s for account %s: %s", rule.rule_id, acc_id, e)

        db.commit()
        return persisted_records

    def _upsert_finding(
        self,
        db: Session,
        organization_id: str,
        account_id: str,
        finding: ScanFinding,
    ) -> OptimizationRecommendation:
        existing = (
            db.query(OptimizationRecommendation)
            .filter(
                OptimizationRecommendation.organization_id == organization_id,
                OptimizationRecommendation.rule_id == finding.rule_id,
                OptimizationRecommendation.resource_id == finding.resource_id,
                OptimizationRecommendation.account_id == account_id,
            )
            .first()
        )

        curr_cost = Decimal(str(round(finding.current_monthly_cost, 4)))
        mo_savings = Decimal(str(round(finding.estimated_monthly_savings, 4)))
        ann_savings = mo_savings * Decimal("12.0")
        pct = Decimal(str(round((finding.estimated_monthly_savings / finding.current_monthly_cost * 100), 2))) if finding.current_monthly_cost > 0 else Decimal("100.00")

        if existing:
            existing.current_monthly_cost = curr_cost
            existing.estimated_monthly_savings = mo_savings
            existing.estimated_annual_savings = ann_savings
            existing.savings_percentage = pct
            existing.reason = finding.description
            existing.recommendation = finding.title
            existing.action_required = finding.remediation_steps or "Review resource utilization and apply suggested optimizations."
            existing.remediation_code = finding.remediation_code
            existing.implementation_effort = finding.implementation_effort
            existing.operational_risk = finding.operational_risk
            existing.production_safety_score = finding.production_safety_score
            return existing

        new_rec = OptimizationRecommendation(
            organization_id=organization_id,
            rule_id=finding.rule_id,
            rule_name=finding.title,
            account_id=account_id,
            region=finding.region or "us-east-1",
            service=finding.resource_type,
            resource_id=finding.resource_id,
            resource_name=finding.resource_name or finding.resource_id,
            current_monthly_cost=curr_cost,
            estimated_monthly_savings=mo_savings,
            estimated_annual_savings=ann_savings,
            savings_percentage=pct,
            priority=finding.severity,
            confidence=finding.confidence,
            validation_status="Requires validation",
            reason=finding.description,
            recommendation=finding.title,
            action_required=finding.remediation_steps or "Review resource utilization and apply suggested optimizations.",
            remediation_code=finding.remediation_code,
            implementation_effort=finding.implementation_effort,
            operational_risk=finding.operational_risk,
            production_safety_score=finding.production_safety_score,
        )
        db.add(new_rec)
        return new_rec

    def _upsert_rule_recommendation(
        self,
        db: Session,
        organization_id: str,
        r: Recommendation,
    ) -> OptimizationRecommendation:
        existing = (
            db.query(OptimizationRecommendation)
            .filter(
                OptimizationRecommendation.organization_id == organization_id,
                OptimizationRecommendation.rule_id == r.rule_id,
                OptimizationRecommendation.resource_id == r.resource_id,
                OptimizationRecommendation.account_id == r.account_id,
            )
            .first()
        )

        if existing:
            existing.current_monthly_cost = r.current_monthly_cost
            existing.estimated_monthly_savings = r.estimated_monthly_savings
            existing.estimated_annual_savings = r.estimated_annual_savings
            existing.savings_percentage = r.savings_percentage
            existing.reason = r.reason
            existing.recommendation = r.recommendation
        remediation = self._generate_rule_cli(r)
        effort = "low" if r.priority in ("LOW", "MEDIUM") else "medium"
        safety = 95 if "Snapshot" in r.rule_id or "EBS" in r.rule_id or "GP3" in r.rule_id else 85

        if existing:
            existing.current_monthly_cost = r.current_monthly_cost
            existing.estimated_monthly_savings = r.estimated_monthly_savings
            existing.estimated_annual_savings = r.estimated_annual_savings
            existing.savings_percentage = r.savings_percentage
            existing.reason = r.reason
            existing.recommendation = r.recommendation
            existing.action_required = r.action_required
            existing.remediation_code = remediation
            existing.implementation_effort = effort
            existing.operational_risk = "low"
            existing.production_safety_score = safety
            return existing

        new_rec = OptimizationRecommendation(
            organization_id=organization_id,
            rule_id=r.rule_id,
            rule_name=r.rule_name,
            account_id=r.account_id,
            region=r.region,
            service=r.service,
            resource_id=r.resource_id,
            resource_name=r.resource_name,
            current_monthly_cost=r.current_monthly_cost,
            estimated_monthly_savings=r.estimated_monthly_savings,
            estimated_annual_savings=r.estimated_annual_savings,
            savings_percentage=r.savings_percentage,
            priority=r.priority,
            confidence=r.confidence,
            validation_status=r.validation_status,
            reason=r.reason,
            recommendation=r.recommendation,
            action_required=r.action_required,
            remediation_code=remediation,
            implementation_effort=effort,
            operational_risk="low",
            production_safety_score=safety,
        )
        db.add(new_rec)
        return new_rec

    def _generate_rule_cli(self, r: Recommendation) -> str:
        rid = r.resource_id
        reg = r.region or "us-east-1"
        rname = r.rule_name.lower()
        if "EC2-001" in r.rule_id or "idle ec2" in rname or "ec2 idle" in rname:
            return f"aws ec2 stop-instances --instance-ids {rid} --region {reg}"
        if "EC2-002" in r.rule_id or "rightsizing" in rname:
            return f"aws ec2 modify-instance-attribute --instance-id {rid} --instance-type t4g.medium --region {reg}"
        if "EBS" in r.rule_id or "ebs" in rname or "volume" in rname:
            return f"aws ec2 create-snapshot --volume-id {rid} --description 'Backup before deletion' --region {reg} && aws ec2 delete-volume --volume-id {rid} --region {reg}"
        if "RDS" in r.rule_id or "rds" in rname or "database" in rname:
            return f"aws rds modify-db-instance --db-instance-identifier {rid} --db-instance-class db.t4g.medium --apply-immediately --region {reg}"
        if "S3" in r.rule_id or "s3" in rname or "bucket" in rname:
            return f"aws s3api put-bucket-lifecycle-configuration --bucket {rid} --lifecycle-configuration '{{\"Rules\":[{{\"ID\":\"IntelligentTiering\",\"Status\":\"Enabled\",\"Filter\":{{\"Prefix\":\"\"}},\"Transitions\":[{{\"Days\":30,\"StorageClass\":\"INTELLIGENT_TIERING\"}}]}}]}}'"
        if "NAT" in r.rule_id or "nat gateway" in rname:
            return f"aws ec2 delete-nat-gateway --nat-gateway-id {rid} --region {reg}"
        if "CW" in r.rule_id or "cloudwatch" in rname:
            return f"aws logs put-retention-policy --log-group-name {rid} --retention-in-days 30"
        if "SNAP" in r.rule_id or "snapshot" in rname:
            return f"aws ec2 delete-snapshot --snapshot-id {rid} --region {reg}"
        return f"# Remediation for {r.rule_id} on {rid}\n# Action: {r.action_required}"

    @staticmethod
    def get_summary(
        db: Session,
        account_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates total monthly and annual potential savings."""
        query = db.query(OptimizationRecommendation)
        if organization_id:
            query = query.filter(OptimizationRecommendation.organization_id == organization_id)
        if account_id and account_id != "all":
            query = query.filter(OptimizationRecommendation.account_id == account_id)

        all_recs = query.all()
        monthly = sum((r.estimated_monthly_savings for r in all_recs), Decimal("0.0000"))
        annual = sum((r.estimated_annual_savings for r in all_recs), Decimal("0.0000"))

        by_priority: Dict[str, Any] = {}
        by_confidence: Dict[str, Any] = {}
        by_service: Dict[str, Any] = {}
        for r in all_recs:
            p = r.priority or "LOW"
            by_priority[p] = by_priority.get(p, Decimal("0.0000")) + (r.estimated_monthly_savings or Decimal("0.0000"))
            c = r.confidence or "Estimated"
            by_confidence[c] = by_confidence.get(c, Decimal("0.0000")) + (r.estimated_monthly_savings or Decimal("0.0000"))
            s = r.service or "Other"
            by_service[s] = by_service.get(s, Decimal("0.0000")) + (r.estimated_monthly_savings or Decimal("0.0000"))

        return {
            "total_monthly_savings": monthly,
            "total_annual_savings": annual,
            "total_recommendations": len(all_recs),
            "by_priority": by_priority,
            "by_confidence": by_confidence,
            "by_service": by_service,
            "high_priority_count": sum((1 for r in all_recs if r.priority == "HIGH")),
            "medium_priority_count": sum((1 for r in all_recs if r.priority == "MEDIUM")),
            "low_priority_count": sum((1 for r in all_recs if r.priority == "LOW")),
        }
